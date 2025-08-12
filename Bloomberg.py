import blpapi
import time
import schedule
import datetime
import pandas as pd

# --- Configuration ---
# Define the securities and data fields you want to fetch.
# These are examples for critical metals. You can customize them.
SECURITIES = [
    "LTHCUSLNER Index",  # Lithium Carbonate Price Index
    "LMCADS03 Comdty",  # LME Cobalt Price
    "LMCADS03 Comdty",  # LME Copper Price
    "LMNIDS03 Comdty",  # LME Nickel Price
    "BMAPRRE Index"  # Bloomberg Rare Earths Index
]
FIELDS = [
    "PX_LAST",  # Last Price
    "BID",  # Bid Price
    "ASK",  # Ask Price
    "PX_VOLUME",  # Trading Volume
    "NAME",  # Security Name
    "CRNCY"  # Currency
]

# Bloomberg API connection details (usually localhost if running on the same machine as the terminal)
HOST = 'localhost'
PORT = 8194


# --- Bloomberg Data Fetching Function ---

def fetch_bloomberg_data():
    """
    Connects to the Bloomberg API, requests reference data, and returns it as a pandas DataFrame.
    """
    print(f"[{datetime.datetime.now()}] Starting Bloomberg data fetch for critical metals...")

    # Define session options
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(HOST)
    sessionOptions.setServerPort(PORT)

    # Create a Session
    session = blpapi.Session(sessionOptions)

    # Start a Session
    if not session.start():
        print("Failed to start session.")
        return None

    try:
        # Open the Reference Data Service
        if not session.openService("//blp/refdata"):
            print("Failed to open //blp/refdata")
            return None

        refDataService = session.getService("//blp/refdata")

        # Create and fill the request
        request = refDataService.createRequest("ReferenceDataRequest")

        # Append securities and fields to the request
        for security in SECURITIES:
            request.append("securities", security)
        for field in FIELDS:
            request.append("fields", field)

        print("Sending Request:", request)
        # Send the request
        session.sendRequest(request)

        # Process the response
        data = []
        while True:
            ev = session.nextEvent(500)  # Timeout in milliseconds
            if ev.eventType() == blpapi.Event.RESPONSE or ev.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                for msg in ev:
                    securityData = msg.getElement("securityData")
                    for sec_data_point in securityData.values():
                        security_name = sec_data_point.getElementAsString("security")
                        fieldData = sec_data_point.getElement("fieldData")
                        row = {"Security": security_name}
                        for field in FIELDS:
                            if fieldData.hasElement(field):
                                # Use getElementAsString for simplicity, but for numerics, other methods exist
                                row[field] = fieldData.getElementAsString(field)
                            else:
                                row[field] = "N/A"
                        data.append(row)

            if ev.eventType() == blpapi.Event.RESPONSE:
                # This is the final event for the request
                break

        # Convert data to a pandas DataFrame
        df = pd.DataFrame(data)
        print("Successfully fetched data:")
        print(df)

        # You can now save this data to a CSV, database, or perform other actions
        # For example, saving to a CSV with a timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"critical_metals_data_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # Stop the session
        session.stop()
        print("Session stopped.")


# --- Main Scheduling Logic ---

def job():
    """The job function that will be scheduled."""
    print(f"Running scheduled job at {datetime.datetime.now()}...")
    fetch_bloomberg_data()


if __name__ == "__main__":
    # For testing, we run the job immediately instead of scheduling it.
    print("Script started. Running data fetch immediately for testing...")
    job()
    print("Script finished.")
