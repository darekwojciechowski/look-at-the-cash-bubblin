# 💰 Look at the cash bubblin

![Python](https://img.shields.io/badge/Python-3.13+-blue?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2.3+-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2.2.0+-013243?style=flat-square&logo=numpy&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-8.3.4+-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-95%25-success?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## 🌟 Overview

💰✨ Getting that financial flow just right...

> *One in the hand, one in the bag, bubblin' (look at you go)*
>
> *Look at the cash, look at the cash bubblin' (okay you bubblin')*
>
> -- *Anderson .Paak - Bubblin'*

## ✨ Key Features
- **Automated Categorization**: Classifies transactions into predefined categories.
- **Data Cleaning**: Standardizes and cleans transaction descriptions.
- **Google Sheets Export**: Prepares and exports data in a format compatible with Google Sheets.
- **Unassigned Transactions**: Identifies and exports uncategorized transactions for manual review.
- **Location Processing**: Integrates with Google Maps for transaction location data.

## 🛠️ Tech Stack
- **Language**: `Python`
- **Libraries**: `pandas`, `logging`
- **Tools**: `CSV processing`, `Google Sheets integration`, `Google Maps links generation`
- **Testing**: `pytest`

## 🏦 Supported Banks
- **PKO**: Fully supported for importing and categorizing transactions.

## 📊 System Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdkYXJrJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyMxZjI5MzcnLCAnbWFpbkJrZyc6ICcjMWYyOTM3JywgJ2NsdXN0ZXJCa2cnOiAnIzExMTgyNycsICdjbHVzdGVyQm9yZGVyJzogJyMzNzQxNTEnLCAnbGluZUNvbG9yJzogJyM5Y2EzYWYnLCAnZm9udEZhbWlseSc6ICdTZWdvZSBVSSwgc2Fucy1zZXJpZicsICdlZGdlTGFiZWxCYWNrZ3JvdW5kJzogJyMxMTE4MjcnIH19fSUlCmdyYXBoIExSCiAgICBzdWJncmFwaCBJbnB1dCBbIiZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwO0RhdGEgSW5wdXQmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsiXQogICAgICAgIGRpcmVjdGlvbiBUQgogICAgICAgIEFbQmFuayBDU1ZdOjo6aW5wdXQKICAgIGVuZAoKICAgIHN1YmdyYXBoIFByb2Nlc3MgWyImbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDtQcm9jZXNzaW5nIFBpcGVsaW5lJm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Il0KICAgICAgICBkaXJlY3Rpb24gVEIKICAgICAgICBCKERhdGEgSW1wb3J0ZXIpOjo6cHJvY2VzcwogICAgICAgIEN7UGFuZGFzIERhdGFGcmFtZX06Ojpwcm9jZXNzCiAgICAgICAgRFtEYXRhIENsZWFuZXJdOjo6cHJvY2VzcwogICAgICAgIEVbQ2F0ZWdvcnkgTWFwcGVyXTo6OnByb2Nlc3MKICAgICAgICBGW0xvY2F0aW9uIFByb2Nlc3Nvcl06Ojpwcm9jZXNzCiAgICBlbmQKCiAgICBzdWJncmFwaCBPdXRwdXQgWyImbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDtEYXRhIE91dHB1dCZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyJdCiAgICAgICAgZGlyZWN0aW9uIFRCCiAgICAgICAgR1tHb29nbGUgU2hlZXRzIENTVl06OjpvdXRwdXQKICAgICAgICBIW1VuYXNzaWduZWQgVHJhbnNhY3Rpb25zXTo6Om91dHB1dAogICAgICAgIElbR29vZ2xlIE1hcHMgTGlua3NdOjo6b3V0cHV0CiAgICBlbmQKCiAgICBBIC0tPnxSZWFkfCBCCiAgICBCIC0tPnxQYXJzZXwgQwogICAgQyAtLT58Q2xlYW58IEQKICAgIEQgLS0-fENhdGVnb3JpemV8IEUKICAgIEUgLS0-fExvY2F0aW9ufCBGCiAgICBGIC0tPnxFeHBvcnR8IEcKICAgIEUgLS4tPnxGaWx0ZXJ8IEgKICAgIEYgLS0-fEdlbmVyYXRlfCBJCgogICAgY2xhc3NEZWYgaW5wdXQgZmlsbDojMTcyNTU0LHN0cm9rZTojNjBhNWZhLHN0cm9rZS13aWR0aDoycHgsY29sb3I6I2RiZWFmZSxyeDo4LHJ5Ojg7CiAgICBjbGFzc0RlZiBwcm9jZXNzIGZpbGw6IzJlMTA2NSxzdHJva2U6I2E3OGJmYSxzdHJva2Utd2lkdGg6MnB4LGNvbG9yOiNmM2U4ZmYscng6OCxyeTo4OwogICAgY2xhc3NEZWYgb3V0cHV0IGZpbGw6IzA2NGUzYixzdHJva2U6IzM0ZDM5OSxzdHJva2Utd2lkdGg6MnB4LGNvbG9yOiNkMWZhZTUscng6OCxyeTo4OwogICAgc3R5bGUgSW5wdXQgZmlsbDojMTExODI3LHN0cm9rZTojMzc0MTUxLHN0cm9rZS13aWR0aDoxcHgscng6MTAscnk6MTAKICAgIHN0eWxlIFByb2Nlc3MgZmlsbDojMTExODI3LHN0cm9rZTojMzc0MTUxLHN0cm9rZS13aWR0aDoxcHgscng6MTAscnk6MTAKICAgIHN0eWxlIE91dHB1dCBmaWxsOiMxMTE4Mjcsc3Ryb2tlOiMzNzQxNTEsc3Ryb2tlLXdpZHRoOjFweCxyeDoxMCxyeToxMA==">
  <img alt="System Architecture" src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNmZmYnLCAnbWFpbkJrZyc6ICcjZmZmJywgJ2NsdXN0ZXJCa2cnOiAnI2Y5ZmFmYicsICdjbHVzdGVyQm9yZGVyJzogJyNlNWU3ZWInLCAnbGluZUNvbG9yJzogJyM2YjcyODAnLCAnZm9udEZhbWlseSc6ICdTZWdvZSBVSSwgc2Fucy1zZXJpZicsICdlZGdlTGFiZWxCYWNrZ3JvdW5kJzogJyNmOWZhZmInIH19fSUlCmdyYXBoIExSCiAgICBzdWJncmFwaCBJbnB1dCBbIiZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwO0RhdGEgSW5wdXQmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsiXQogICAgICAgIGRpcmVjdGlvbiBUQgogICAgICAgIEFbQmFuayBDU1ZdOjo6aW5wdXQKICAgIGVuZAoKICAgIHN1YmdyYXBoIFByb2Nlc3MgWyImbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDtQcm9jZXNzaW5nIFBpcGVsaW5lJm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Jm5ic3A7Il0KICAgICAgICBkaXJlY3Rpb24gVEIKICAgICAgICBCKERhdGEgSW1wb3J0ZXIpOjo6cHJvY2VzcwogICAgICAgIEN7UGFuZGFzIERhdGFGcmFtZX06Ojpwcm9jZXNzCiAgICAgICAgRFtEYXRhIENsZWFuZXJdOjo6cHJvY2VzcwogICAgICAgIEVbQ2F0ZWdvcnkgTWFwcGVyXTo6OnByb2Nlc3MKICAgICAgICBGW0xvY2F0aW9uIFByb2Nlc3Nvcl06Ojpwcm9jZXNzCiAgICBlbmQKCiAgICBzdWJncmFwaCBPdXRwdXQgWyImbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDsmbmJzcDtEYXRhIE91dHB1dCZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyZuYnNwOyJdCiAgICAgICAgZGlyZWN0aW9uIFRCCiAgICAgICAgR1tHb29nbGUgU2hlZXRzIENTVl06OjpvdXRwdXQKICAgICAgICBIW1VuYXNzaWduZWQgVHJhbnNhY3Rpb25zXTo6Om91dHB1dAogICAgICAgIElbR29vZ2xlIE1hcHMgTGlua3NdOjo6b3V0cHV0CiAgICBlbmQKCiAgICBBIC0tPnxSZWFkfCBCCiAgICBCIC0tPnxQYXJzZXwgQwogICAgQyAtLT58Q2xlYW58IEQKICAgIEQgLS0-fENhdGVnb3JpemV8IEUKICAgIEUgLS0-fExvY2F0aW9ufCBGCiAgICBGIC0tPnxFeHBvcnR8IEcKICAgIEUgLS4tPnxGaWx0ZXJ8IEgKICAgIEYgLS0-fEdlbmVyYXRlfCBJCgogICAgY2xhc3NEZWYgaW5wdXQgZmlsbDojZWZmNmZmLHN0cm9rZTojM2I4MmY2LHN0cm9rZS13aWR0aDoycHgsY29sb3I6IzFlM2E4YSxyeDo4LHJ5Ojg7CiAgICBjbGFzc0RlZiBwcm9jZXNzIGZpbGw6I2Y1ZjNmZixzdHJva2U6IzhiNWNmNixzdHJva2Utd2lkdGg6MnB4LGNvbG9yOiM0YzFkOTUscng6OCxyeTo4OwogICAgY2xhc3NEZWYgb3V0cHV0IGZpbGw6I2VjZmRmNSxzdHJva2U6IzEwYjk4MSxzdHJva2Utd2lkdGg6MnB4LGNvbG9yOiMwNjRlM2Iscng6OCxyeTo4OwogICAgc3R5bGUgSW5wdXQgZmlsbDojZjlmYWZiLHN0cm9rZTojZTVlN2ViLHN0cm9rZS13aWR0aDoxcHgscng6MTAscnk6MTAKICAgIHN0eWxlIFByb2Nlc3MgZmlsbDojZjlmYWZiLHN0cm9rZTojZTVlN2ViLHN0cm9rZS13aWR0aDoxcHgscng6MTAscnk6MTAKICAgIHN0eWxlIE91dHB1dCBmaWxsOiNmOWZhZmIsc3Ryb2tlOiNlNWU3ZWIsc3Ryb2tlLXdpZHRoOjFweCxyeDoxMCxyeToxMA==">
</picture>

The system follows a three-layer architecture:
- **Data Input**: Reads bank CSV transactions with Polish encoding support
- **Processing Pipeline**: Cleans data → Maps categories → Processes locations → Generates maps links
- **Data Output**: Exports to Google Sheets format, identifies unassigned transactions, and creates location links

## 🧪 Testing & Quality Assurance
This project maintains high code quality through comprehensive testing practices:
- **Unit Tests**: Full test coverage using `pytest` for all core modules
- **Test-Driven Development**: Ensures reliability and maintainability
- **Automated Testing**: CI/CD-ready test suite for continuous validation
- **Code Coverage**: Tracked with detailed coverage reports

## 🚀 How to Use
1. Place your transaction CSV file in the `data/` directory.
2. Fill the `data_processing/category.py` file with your personal category data.
3. Run the main script:
   ```bash
   python main.py
   ```
4. Processed data will be available in `for_google_spreadsheet.csv`.

## 🤔 Why I Built This

We all want a clearer picture of our finances. I created this project to simplify that process. By automatically categorizing your bank transactions, it gives you effortless insights into your spending habits. This means you can stop guessing, start seeing patterns, and make better choices that improve your financial health.


