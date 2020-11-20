from arcgis.gis import GIS
from getpass import getpass
import logging
from datetime import datetime
import time

logging.basicConfig(filename='{:%Y-%m-%d}-migration-prod.log'.format(datetime.now()),format='%(asctime)s %(message)s', level=logging.INFO)

gis = GIS("https://<shortname>.maps.arcgis.com", "<username>", "<password>")
i=0

print('Login successful!')
print(' server:', gis.properties.name)
print(' user:', gis.properties.user.username)
print(' role:', gis.properties.user.role)

proLicense = gis.admin.license.get('ArcGIS Pro')


# Get extensions for pro
licEntitlements = list(proLicense.properties['provision']['orgEntitlements']['entitlements'].keys())
# Remove Pro itself since it is now included in GIS Pro user type

# Get all users
users = gis.users.search(max_users=9999)

#Start at offset (useful if previous iteration broke.
#users = users[200:]

def batchmaker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def assignLicenses(user,entitlements):
    userEntitlements = entitlements
    if 'desktopAdvN' in userEntitlements:
        userEntitlements.remove('desktopAdvN')
    # Assign ArcGIS Pro licenses and extensions
    logging.info(user.username + " has no licenses")
    flag = 1
    while flag != 0:
        try:
            proLicense.assign(username=user.username, entitlements=userEntitlements, suppress_email=True)
            logging.info("Assigning licenses for " + user.username + "...")
            flag = 0
        except Exception as e:
            print(e)
            flag = 1
            logging.info("Failed assigning licenses for " + user.username + "...\n Trying again in 5 minutes.")
            time.sleep(300)

def revokeLicenses(user,entitlements):
    flag = 1
    while flag != 0:
        try:
            proLicense.revoke(username=user.username, entitlements=entitlements, suppress_email=True)
            logging.info("Removing licenses for " + user.username + "...")
            flag = 0
        except Exception as e:
            print(e)
            flag = 1
            logging.info(
                "Failed removing licenses for " + user.username + "...\n Trying again in 5 minutes.")
            time.sleep(300)

# loop through all users
for user_batch in batchmaker(users, 100):
   for user in user_batch:
       #Only process SSO users
        if user.username.find('ucdavis.edu_ucdavis') >= 0:
            #logging.info(user.username + ": " + user.userLicenseTypeId)
            if user.userLicenseTypeId != "GISProfessionalAdvUT":
                # Change user type for each user
                logging.info("Changing user type for " + user.username +" to GIS Professional.")
                user.update_license_type('GISProfessionalAdvUT')
            if user.userLicenseTypeId == 'GISProfessionalAdvUT':
                userlicense = proLicense.user_entitlement(user.username)
                if len(userlicense) == 0:
                    assignLicenses(user, licEntitlements)
                if len(userlicense) > 0:
                    if 'desktopAdvN' in userlicense['entitlements']:
                        revokeLicenses(user, licEntitlements)
                        assignLicenses(user, licEntitlements)
                    else:
                        logging.info(user.username + " has correct licenses")
   i=i+1
   print("Batch: " + str(i*100))
   logging.info("Proccessed " + str(i*100) + " users.")

