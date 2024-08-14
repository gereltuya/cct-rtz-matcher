import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from datetime import datetime
import hmac

def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False):
        return True
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

def get_df(csv_url):
  return pd.read_csv(csv_url).applymap(str)

def get_unique_values(list_to_process):
  return list(dict.fromkeys(list_to_process))

def hash_columns(df_to_hash, column_key, column_value):
  hash_dict = {}
  for index, row in df_to_hash.iterrows():
    if row[column_key] not in hash_dict.keys():
      hash_dict[row[column_key]] = [row[column_value]]
    else:
      hash_dict[row[column_key]].append(row[column_value])
  for key in hash_dict.keys():
    hash_dict[key] = "; ".join(get_unique_values(hash_dict[key]))
  return hash_dict

def split_name(name_to_split):
  return name_to_split.replace(",", " ").lower().split()

def hash_abb(df_to_hash, column_key, column_value):
  hash_dict = {}
  for index, row in df_to_hash.iterrows():
    if row[column_key] not in hash_dict.keys():
      hash_dict[row[column_key]] = split_name(row[column_value])
    else:
      for abb in split_name(row[column_value]):
        hash_dict[row[column_key]].append(abb)
  for key in hash_dict.keys():
    hash_dict[key] = get_unique_values(hash_dict[key])
    return hash_dict

hash_match_ref_countries = {"Aruba": "Netherlands",
                            "Bahamas": "The Bahamas",
                            "Bermuda": "United Kingdom",
                            "Bolivia (Plurinational State of)": "Bolivia",
                            "Bonaire, Sint Eustatius and Saba": "Netherlands",
                            "Brunei Darussalam": "Brunei",
                            "Cayman Islands": "United Kingdom",
                            "Cook Islands": "New Zealand",
                            "Curaçao": "Netherlands",
                            "Gibraltar": "United Kingdom",
                            "Guam": "United States of America",
                            "Guernsey": "United Kingdom",
                            "Hong Kong": "China",
                            "Isle of Man": "United Kingdom",
                            "Jersey": "United Kingdom",
                            "Korea (Republic of)": "South Korea",
                            "North Macedonia": "Macedonia",
                            "Puerto Rico": "United States of America",
                            "Russian Federation": "Russia",
                            "Serbia": "Republic of Serbia",
                            "Sint Maarten": "Netherlands",
                            "Taiwan (Province of China)": "Taiwan, a province of China",
                            "Türkiye": "Turkey",
                            "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
                            "Viet Nam": "Vietnam",
                            "Virgin Islands (British)": "United Kingdom",
                            "Virgin Islands (U.S.)": "United States of America",
                            "Czech Republic": "Czechia",
                            "Taiwan": "Taiwan, a province of China",
                            "United States": "United States of America"}

entity_column_rtz = "Name"
entity_column_clean = "Name clean"
country_column_rtz = "Country of HQ"
country_column_clean = "Country ref"
type_column_rtz = "Type"

def clean_df(df_to_clean, entity_column, country_column, hash_to_use):
  df_to_clean[entity_column_clean] = pd.Series(dtype="object")
  df_to_clean[country_column_clean] = pd.Series(dtype="object")
  names_clean = []
  countries_ref = []
  for index, row in df_to_clean.iterrows():
    name_words = split_name(row[entity_column])
    name_words_clean = []
    name_words_clean_v2 = []
    name_clean = ""
    if row[country_column] in hash_match_ref_countries.keys():
      country_ref = hash_match_ref_countries[row[country_column]]
    else:
      country_ref = row[country_column]
    countries_ref.append(country_ref)
    if country_ref not in hash_to_use.keys():
      for name_word in name_words:
        if name_word not in hash_to_use["Global"]:
          name_words_clean.append(name_word)
        else:
          pass
      name_clean = " ".join(name_words_clean)
    else:
      for name_word in name_words:
        if name_word not in hash_to_use[country_ref]:
          name_words_clean.append(name_word)
        else:
          pass
      for name_word in name_words_clean:
        if name_word not in hash_to_use["Global"]:
          name_words_clean_v2.append(name_word)
        else:
          pass
      name_clean = " ".join(name_words_clean_v2)
    if name_clean == "":
      names_clean.append(" ".join(name_words))
    else:
      names_clean.append(name_clean)
  df_to_clean[entity_column_clean] = names_clean
  df_to_clean[country_column_clean] = countries_ref
  return df_to_clean

def clean_df_without_countries(df_to_clean, entity_column, hash_to_use):
  df_to_clean[entity_column_clean] = pd.Series(dtype="object")
  df_to_clean[country_column_clean] = pd.Series(dtype="object")
  names_clean = []
  countries_ref = []
  for index, row in df_to_clean.iterrows():
    name_words = split_name(row[entity_column])
    name_words_clean = []
    name_clean = ""
    country_ref = "Global"
    countries_ref.append(country_ref)
    for name_word in name_words:
      if name_word not in hash_to_use[country_ref]:
        name_words_clean.append(name_word)
      else:
        pass
    name_clean = " ".join(name_words_clean)
    if name_clean == "":
      names_clean.append(" ".join(name_words))
    else:
      names_clean.append(name_clean)
  df_to_clean[entity_column_clean] = names_clean
  df_to_clean[country_column_clean] = countries_ref
  return df_to_clean

def match_names(name, choices, scorer=fuzz.ratio):
  best_match = process.extractOne(name, choices, scorer=scorer)
  return best_match

def match_dfs(df_rtz, df_input, hash_names_rtz, hash_countries_rtz, hash_types_rtz):
  df_rtz[entity_column_clean] = df_rtz[entity_column_clean].astype(str)
  df_input[entity_column_clean] = df_input[entity_column_clean].astype(str)
  matches = []
  for index, row in df_input.iterrows():
    name = row[entity_column_clean]
    column_rtz = df_rtz[(df_rtz[country_column_rtz] == row[country_column_clean]) | (df_rtz[country_column_rtz] == "")][entity_column_clean]
    match = match_names(name, column_rtz)
    if match[1] == 100:
      match_status = "Fully matched"
    elif match[1] >= 90:
      match_status = "Likely a match, but manual check needed"
    else:
      match_status = "Unlikely a match, but manual check needed"
    matches.append((match[0], hash_names_rtz[match[0]], hash_countries_rtz[match[0]], hash_types_rtz[match[0]], match[1], match_status))
  df_matches = pd.DataFrame(matches, columns=["Name clean RtZ", "Name RtZ", "Country RtZ", "Type RtZ", "Match percentage", "Match status"])
  df_input.reset_index(drop=True, inplace=True)
  df_matches.reset_index(drop=True, inplace=True)
  df_matches_full = pd.concat([df_input, df_matches], axis=1)
  return df_matches_full

def match_dfs_without_countries(df_rtz, df_input, hash_names_rtz, hash_countries_rtz, hash_types_rtz):
  df_rtz[entity_column_clean] = df_rtz[entity_column_clean].astype(str)
  df_input[entity_column_clean] = df_input[entity_column_clean].astype(str)
  matches = []
  for index, row in df_input.iterrows():
    name = row[entity_column_clean]
    column_rtz = df_rtz[entity_column_clean]
    match = match_names(name, column_rtz)
    if match[1] == 100:
      match_status = "Fully matched"
    elif match[1] >= 90:
      match_status = "Likely a match, but manual check needed"
    else:
      match_status = "Unlikely a match, but manual check needed"
    matches.append((match[0], hash_names_rtz[match[0]], hash_countries_rtz[match[0]], hash_types_rtz[match[0]], match[1], match_status))
  df_matches = pd.DataFrame(matches, columns=["Name clean RtZ", "Name RtZ", "Country RtZ", "Type RtZ", "Match percentage", "Match status"])
  df_input.reset_index(drop=True, inplace=True)
  df_matches.reset_index(drop=True, inplace=True)
  df_matches_full = pd.concat([df_input, df_matches], axis=1)
  return df_matches_full

st.sidebar.write("Please note that this matching tool is designed to reduce the amount of manual work involved in identifying who is in the Race to Zero.")
st.sidebar.write("However, it is not intended to completely eliminate manual work.")
st.sidebar.write("We encourage you to provide feedback to help improve its results.")
st.sidebar.link_button("Send feedback", "https://forms.gle/c8HZtr9LGkN5U6nX9", type="primary")

st.title("Match your entity list against the latest Race to Zero member list")
st.header("Data is up-to-date as of August 14, 2024, and the matching method is version 4.")

st.divider()
st.subheader("1. Downloading the Race to Zero database and processing it...")
df = get_df("https://github.com/gereltuya/cct-rtz-matcher/raw/main/data/RtZ%20Participants%20-%20April%202024%20-%20Clean.csv")
hash_names = hash_columns(df, entity_column_clean, entity_column_rtz)
hash_countries = hash_columns(df, entity_column_clean, country_column_rtz)
hash_types = hash_columns(df, entity_column_clean, type_column_rtz)
st.caption("Done!")
public_columns = ["Name", "Type", "Country of HQ", "UN Region", "Sector \n(if applicable)", "Join Date (DD/MM/YYYY)"]
st.dataframe(df[public_columns])

st.divider()
st.subheader("2. Downloading the entity legal form list and processing it...")
df_elf = get_df("https://github.com/gereltuya/cct-rtz-matcher/raw/main/data/ELF%20v1.5%20+%20LET%20+%20Manual.csv")
hash_elf = hash_abb(df_elf, "Country", "Abbreviation")
hash_elf_without_countries = hash_abb(df_elf, "Country Global", "Abbreviation")
st.caption("Done!")

st.divider()
st.subheader("3. Upload the list you want to match against the Race to Zero database:")
uploaded_file = st.file_uploader("Upload your data in CSV format.")
if uploaded_file is not None:
  df_to_match = pd.read_csv(uploaded_file)
  st.dataframe(df_to_match)
  country_status = st.radio("Does your data include the countries for which the legal entities are registered?", ["Yes", "No"])
  if country_status == "Yes":
    country_column_name = st.text_input("What is the column name for **countries** in your data? Please type it exactly as it is and press **Enter**, otherwise the next steps might result in errors.", "Country")
    entity_column_name = st.text_input("What is the column name for **entities** in your data? Please type it exactly as it is and press **Enter**, otherwise the next steps might result in errors.", "Name")
    
    st.divider()
    st.subheader("4. Downloading the reference country list and processing it...")
    df_ref = get_df("https://github.com/gereltuya/cct-rtz-matcher/raw/main/data/Reference%20list%20-%20Countries.csv")
    ref_countries = df_ref["Countries in dashboard map"].unique().tolist()
    match_countries = df_to_match[country_column_name].unique().tolist()
    countries_to_map = [country for country in match_countries if country not in ref_countries]
    if len(countries_to_map) > 0:
      st.write("a) These countries in your data are not in the reference country list:")
      for country in countries_to_map:
        st.write(country)
      st.write("b) These will be mapped according to our predefined mapping list.")
      # st.write(hash_match_ref_countries)
    else:
      st.write("a) All countries in your data are in the reference country list.")
    st.caption("Done!")

    st.divider()
    st.subheader("5. Cleaning uploaded list to match...")
    df_to_match = clean_df(df_to_match, entity_column_name, country_column_name, hash_elf)
    hash_names_to_match = hash_columns(df_to_match, entity_column_clean, entity_column_name)
    hash_countries_to_match = hash_columns(df_to_match, entity_column_clean, country_column_clean)
    st.caption("Done!")

    st.divider()
    st.subheader("6. Matching the uploaded data with the Race to Zero database...")
    df_matches1_full = match_dfs(df, df_to_match, hash_names, hash_countries, hash_types)
    st.caption("Done!")
    st.balloons()

    st.divider()
    st.subheader("7. Match results")
    len_to_match = df_to_match.shape[0]
    st.write(df_matches1_full.groupby(["Match status"]).size().reset_index(name="Count (out of {})".format(len_to_match)))
    df_matches1_filtered = df_matches1_full.drop(columns = ["Name clean", "Country ref", "Name clean RtZ"])
    st.dataframe(df_matches1_filtered)
    current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    st.download_button(label="Download the full results in CSV format", data=df_matches1_full.to_csv().encode("utf-8"), file_name="Race to Zero matches full {}.csv".format(current_datetime), mime="text/csv")

  elif country_status == "No":
    entity_column_name = st.text_input("What is the column name for **entities** in your data? Please type it exactly as it is and press **Enter**, otherwise the next steps might result in errors.", "Name")
    
    st.divider()
    st.subheader("6. Cleaning uploaded list to match...")
    df_to_match = clean_df_without_countries(df_to_match, entity_column_name, hash_elf_without_countries)
    hash_names_to_match = hash_columns(df_to_match, entity_column_clean, entity_column_name)
    hash_countries_to_match = hash_columns(df_to_match, entity_column_clean, country_column_clean)
    st.caption("Done!")

    st.divider()
    st.subheader("6. Matching the uploaded data with the Race to Zero database...")
    df_matches2_full = match_dfs_without_countries(df, df_to_match, hash_names, hash_countries, hash_types)
    st.caption("Done!")
    st.balloons()

    st.divider()
    st.subheader("7. Match results")
    len_to_match = df_to_match.shape[0]
    st.write(df_matches2_full.groupby(["Match status"]).size().reset_index(name="Count (out of {})".format(len_to_match)))
    df_matches2_filtered = df_matches2_full.drop(columns = ["Name clean", "Name clean RtZ"])
    st.dataframe(df_matches2_filtered)
    current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    st.download_button(label="Download the full results in CSV format", data=df_matches2_full.to_csv().encode("utf-8"), file_name="Race to Zero matches full {}.csv".format(current_datetime), mime="text/csv")