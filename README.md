# Sports Betting Odds Parser
This project is a web scraper that parses sports betting odds from various URLs and prints them to stdout as a JSON object. 
The JSON object is a dictionary where the key is the name of the sport and the value is a list of Item objects, which contain detailed information about the betting odds.

## Features
- Parses betting odds for multiple sports.
- Outputs data in JSON format.
- Runs in an infinite loop, updating the odds periodically.

## Installation

1. Clone the repository:<br>
   ```
   git clone https://github.com/yourusername/sports-betting-odds-parser.git
   cd sports-betting-odds-parser
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
## Usage

1. Run the script:
   ```
   python parse_veri_bet.py
   ```
The script will start parsing the betting odds from the specified URLs and print the results to stdout in JSON format.
