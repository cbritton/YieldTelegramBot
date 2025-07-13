import pandas as pd
from dateutil import parser
import requests
import io
from typing import List, Optional
from datetime import datetime
from requests.exceptions import RequestException
from pandas.errors import EmptyDataError
import arrow


class ZacksError(Exception):
    """Base exception class for ZacksEarnings errors"""
    pass

class ZacksRequestError(ZacksError):
    """Raised when there's an error making requests to Zacks"""
    pass

class ZacksParsingError(ZacksError):
    """Raised when there's an error parsing data from Zacks"""
    pass

class ZacksEarnings:
    _ZACKS_URL = 'https://www.zacks.com/stock/quote/{}/detailed-estimates'
    _ZACKS_HEADER = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    }
    
    @staticmethod
    def get_next_earnings_estimate(symbol: str) -> List[tuple]:
        """
        Get the next earnings estimate date for a given stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            
        Returns:
            List[datetime]: List containing the next earnings date if found, empty list otherwise
            
        Raises:
            ZacksRequestError: If there's an error making the request to Zacks
            ZacksParsingError: If there's an error parsing the response data
        """
        try:
            r = requests.get(
                ZacksEarnings._ZACKS_URL.format(symbol.upper()),
                headers=ZacksEarnings._ZACKS_HEADER,
                timeout=10
            )
            r.raise_for_status()
            
            # Try multiple parsing approaches
            try:
                # First attempt: Look for tables containing earnings-related keywords
                all_tables = pd.read_html(r.content)
                for table in all_tables:
                    # Convert table to string to make text searching easier
                    table_str = str(table)
                    if any(keyword in table_str.lower() for keyword in ['next report', 'earnings date', 'next earnings']):
                        # Search through the table for date-like strings
                        for col in table.columns:
                            for val in table[col]:
                                try:
                                    if isinstance(val, str):
                                        date = parser.parse(val, fuzzy=True)
                                        if date > datetime.now():  # Only return future dates
                                            earnings_time = ""
                                            if "BMO" in val:
                                                earnings_time = "BMO"
                                            elif "AMC" in val:
                                                earnings_time = "AMC"
                                            return [(earnings_time,date)]
                                except ValueError:
                                    continue
                
                # Second attempt: Try to find any date-like strings in the HTML
                import re
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(r.content, 'html.parser')
                # Look for common date containers
                date_containers = soup.find_all(['span', 'div', 'td'], 
                    class_=re.compile(r'date|earnings|report', re.I))
                
                for container in date_containers:
                    try:
                        date = parser.parse(container.text, fuzzy=True)
                        if date > datetime.now():  # Only return future dates
                            earnings_time = ""
                            if "BMO" in val:
                                earnings_time = "BMO"
                            elif "AMC" in val:
                                earnings_time = "AMC"
                            return [(earnings_time,date)]
                    except ValueError:
                        continue
                
                return []
                
            except ValueError as e:
                return []
            
        except requests.exceptions.RequestException as e:
            raise ZacksRequestError(f"Failed to fetch data for {symbol}: {str(e)}")
            
        except (ValueError, KeyError, IndexError) as e:
            raise ZacksParsingError(f"Failed to parse earnings data for {symbol}: {str(e)}")
            
        except Exception as e:
            raise ZacksError(f"Unexpected error processing {symbol}: {str(e)}")

    @staticmethod
    def earnings_by_date(date: datetime) -> pd.DataFrame:
        """
        Get all earnings reports for a specific date.
        
        Args:
            date (datetime): The date to get earnings for
            
        Returns:
            pd.DataFrame: DataFrame containing earnings data
            
        Raises:
            ZacksRequestError: If there's an error making the request to Zacks
            ZacksParsingError: If there's an error parsing the response data
        """
        site = 'https://www.zacks.com/research/earnings/earning_export.php?timestamp={}&tab_id=1'
        header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        try:
            print(site.format(int(date.timestamp())))
            ts = 1752642000
                #site.format(int(date.timestamp())),
            url = "https://www.zacks.com/includes/classes/z2_class_calendarfunctions_data.php?calltype=eventscal&date=1752642000&type=1&search_trigger=0&0.437963603109525=&_=1752351153818"
            response = requests.get(
                url,
                headers=header,
                timeout=10
            )
            response.raise_for_status()
            
            df = pd.read_csv(
                io.StringIO(response.content.decode('utf-8')),
                sep='\t'
            )
            
            if df.empty:
                pass
            else:
                pass
                
            return df
            
        except RequestException as e:
            raise ZacksRequestError(f"Failed to fetch earnings data for {date}: {str(e)}")
            
        except EmptyDataError as e:
            return pd.DataFrame()
            
        except Exception as e:
            raise ZacksError(f"Unexpected error processing earnings for {date}: {str(e)}")

def main():
    try:
        # Test earnings by date
        #test_date = parser.parse('July 13, 2025')
        test_date = arrow.get(2025,7,14)
        earnings = ZacksEarnings.earnings_by_date(test_date.datetime)
        print(f'\nEarnings for {test_date.strftime("%B %d, %Y")}:')
        print(earnings)
    except ZacksError as e:
        print(e)
        
    except Exception as e:
        print(e)

    try:
        # Test next earnings estimate
        symbol = 'FAST'
        earnings = ZacksEarnings.get_next_earnings_estimate(symbol)
        if len(earnings) > 0:
            earnings_time, next_earnings_date = earnings[0]
            print(f'\n{symbol} Estimated Earnings Date: {next_earnings_date.strftime("%Y-%m-%d")} {earnings_time}')
        else:
            print("no data")
        
    except ZacksError as e:
        print(e)
        
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()