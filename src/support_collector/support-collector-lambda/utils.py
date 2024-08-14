from datetime import datetime


def convert_time_to_month_year(iso_datetime):
    # Parse the time_created string into a datetime object
    # dt = datetime.strptime(iso_datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
    iso_date = iso_datetime.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso_date)

    # Extract the year and month components
    year = dt.year
    month = dt.month

    # Format the year and month as "YYYY/MM"
    month_year = f"{year}/{month:02d}"

    return month_year
