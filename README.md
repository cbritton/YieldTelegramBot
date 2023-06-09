# YieldTelegramBot
Retrieve yield data from FRED through a Telegram bot.

## Usage
This is a simple Telegram bot that responds to the following commands:
- yield  - this returns a table of the most recent yield rates
- curve  - shows the yield curve on the most recent rates
- spread - shows the spread graph between two maturities, optionally takes an number value for months to plot. For example, /spread 2y 10y 36 plots the difference between the 2 and 10 year going back 36 months. If the month is not provided, the default is 12.


Example response for the table:

<img src="./media/table.jpg" width="25%">

Example response for the yield curve:

<img src="./media/graph.jpg" width="25%">

Example response for the spread curve:

<img src="./media/spread.jpg" width="25%">

## Setup

To set this up, you will need a telegram bot key and a Fred API key (https://fred.stlouisfed.org/docs/api/fred/).  Add these to the .env file.  

On windows, create a virtual environment and install the packages:

`
pip install -r requirement.txt
`

On linux, the requirements file is different due to the library dependency for saving files:

`
pip install -r requirements-linux.txt
`

Start the application on the command line with

`
python main.py
`

Once started, the application polls the Telegram service for messages and response appropriately.

Alternatively, a docker image has been provided to run within a linux environment.
