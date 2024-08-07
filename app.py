import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

st.title("Match your lists against the latest Race to Zero member list")
st.header("Data up-to-date as of August 7, 2024")

st.divider()
st.subheader("1. Downloading the Race to Zero database and processing it...")

rtz_masterlist_url = "https://github.com/gereltuya/cct-rtz-matcher/raw/main/RtZ%20Participants%20-%20April%202024%20-%20Clean.csv"
df = pd.read_csv(rtz_masterlist_url)
df = df.applymap(str)

hash_names = {}
hash_countries = {}
for index, row in df.iterrows():
  if row["Name clean"] not in hash_names.keys():
    hash_names[row["Name clean"]] = [row["Name"]]
    hash_countries[row["Name clean"]] = [row["Country of HQ"]]
  else:
    hash_names[row["Name clean"]].append(row["Name"])
    hash_countries[row["Name clean"]].append(row["Country of HQ"])
for key in hash_names.keys():
  hash_names[key] = "; ".join(list(dict.fromkeys(hash_names[key])))
for key in hash_countries.keys():
  hash_countries[key] = "; ".join(list(dict.fromkeys(hash_countries[key])))

st.caption("Done!")
st.dataframe(df[["Name", "Type", "Country of HQ", "UN Region", "Sector \n(if applicable)", "Join Date (DD/MM/YYYY)"]])

st.divider()
st.subheader("2. Downloading the entity legal form list and processing it...")

elf_let_manual_url = "https://github.com/gereltuya/cct-rtz-matcher/raw/main/ELF%20v1.5%20+%20LET%20+%20Manual.csv"
df_let = pd.read_csv(elf_let_manual_url)
df_let = df_let.applymap(str)

hash_let = {}
for index, row in df_let.iterrows():
  if row["Country"] not in hash_let.keys():
    hash_let[row["Country"]] = row["Abbreviation"].replace(",", " ").lower().split()
  else:
    for abb in row["Abbreviation"].replace(",", " ").lower().split():
      hash_let[row["Country"]].append(abb)
for key in hash_let.keys():
  hash_let[key] = list(dict.fromkeys(hash_let[key]))

st.caption("Done!")

st.divider()
st.subheader("3. Upload the list you want to be matched with the RtZ database:")

uploaded_file = st.file_uploader("Upload a CSV file with 'Company Name' and 'Country' columns for now. You can put 'Global' in the 'Country' column if not specified.")

if uploaded_file is not None:
  df_to_match = pd.read_csv(uploaded_file)
  st.caption("Done!")
  st.dataframe(df_to_match)

  st.divider()
  st.subheader("4. Downloading the reference country list and processing it...")

  ref_countries_url = "https://github.com/gereltuya/cct-rtz-matcher/raw/main/Reference%20list%20-%20Countries.csv"
  df_ref = pd.read_csv(ref_countries_url)
  df_ref = df_ref.applymap(str)

  ref_countries = df_ref["Countries in dashboard map"].unique().tolist()
  match_countries = df_to_match["Country"].unique().tolist()
  st.write("These countries are not in the reference country list:")
  for country in match_countries:
    if country not in ref_countries:
      st.write(country)

  st.write("These will be mapped according to our predefined mapping list:")
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
  st.write(hash_match_ref_countries)
  st.caption("Done!")

  st.divider()
  st.subheader("5. Cleaning uploaded list to match...")

  df_to_match['Name clean'] = pd.Series(dtype='object')
  df_to_match['Country ref'] = pd.Series(dtype='object')
  names_clean = []
  countries_ref = []
  for index, row in df_to_match.iterrows():
    name_words = row["Company Name"].replace(",", " ").lower().split()
    name_words_clean = []
    name_words_clean_v2 = []
    name_clean = ""
    if row["Country"] in hash_match_ref_countries.keys():
      country_ref = hash_match_ref_countries[row["Country"]]
    else:
      country_ref = row["Country"]
    countries_ref.append(country_ref)
    if country_ref not in hash_let.keys():
      for name_word in name_words:
        if name_word not in hash_let["Global"]:
          name_words_clean.append(name_word)
        else:
          pass
      name_clean = " ".join(name_words_clean)
    else:
      for name_word in name_words:
        if name_word not in hash_let[country_ref]:
          name_words_clean.append(name_word)
        else:
          pass
      for name_word in name_words_clean:
        if name_word not in hash_let["Global"]:
          name_words_clean_v2.append(name_word)
        else:
          pass
      name_clean = " ".join(name_words_clean_v2)
    if name_clean == "":
      names_clean.append(" ".join(name_words))
    else:
      names_clean.append(name_clean)
  df_to_match["Name clean"] = names_clean
  df_to_match["Country ref"] = countries_ref

  st.write("Creating hashes of names and countries for later retrieval...")
  hash_names_to_match = {}
  hash_countries_to_match = {}
  for index, row in df_to_match.iterrows():
    if row["Name clean"] not in hash_names_to_match.keys():
      hash_names_to_match[row["Name clean"]] = [row["Company Name"]]
      hash_countries_to_match[row["Name clean"]] = [row["Country ref"]]
    else:
      hash_names_to_match[row["Name clean"]].append(row["Company Name"])
      hash_countries_to_match[row["Name clean"]].append(row["Country ref"])
  for key in hash_names_to_match.keys():
    hash_names_to_match[key] = "; ".join(list(dict.fromkeys(hash_names_to_match[key])))
  for key in hash_countries_to_match.keys():
    hash_countries_to_match[key] = "; ".join(list(dict.fromkeys(hash_countries_to_match[key])))
  st.caption("Done!")

  st.divider()
  st.subheader("6. Matching the uploaded list with RtZ database...")

  df['Name clean'] = df['Name clean'].astype(str)
  df_to_match['Name clean'] = df_to_match['Name clean'].astype(str)
  def match_names(name, choices, scorer=fuzz.ratio):
      best_match = process.extractOne(name, choices, scorer=scorer)
      return best_match
  matches = []
  for index, row in df_to_match.iterrows():
    name = row["Name clean"]
    match = match_names(name, df[(df["Country of HQ"] == row["Country ref"]) | (df["Country of HQ"] == "")]["Name clean"])
    matches.append((match[0], hash_names[match[0]], hash_countries[match[0]], match[1]))
  df_matches1 = pd.DataFrame(matches, columns=['Name clean RtZ', 'Name RtZ', 'Country RtZ', 'Match percentage'])

  df_to_match.reset_index(drop=True, inplace=True)
  df_matches1.reset_index(drop=True, inplace=True)
  df_matches1_full = pd.concat([df_to_match, df_matches1], axis=1)
  df_matches1_full.head(5)
  st.caption("Done!")
  st.dataframe(df_matches1_full)
  st.balloons()

  st.download_button(
    label="Download the result as CSV",
    data=df_matches1_full.to_csv().encode("utf-8"),
    file_name="Race to Zero matches.csv",
    mime="text/csv",)