import ee
import os

def init(user=None):
        sa=os.environ.get('SERVICE_ACCOUNT')
        if sa:
                print "gee.init[ sevice_account ] {}".format(sa)
                credentials = ee.ServiceAccountCredentials(sa, 'privatekey.pem')
                ee.Initialize(credentials)
        else:
                print "gee.init[ user_account ] {}".format(user or '')
                ee.Initialize()
        return True