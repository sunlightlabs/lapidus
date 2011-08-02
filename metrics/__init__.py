import datetime

def daterange(start, end):
    days = (end - start).days + 1
    for i in xrange(days):
        yield start + datetime.timedelta(i)