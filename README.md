# 💰 Look at the cash bubblin

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


