# Ip2Location Database Wrapper Service
Ip2Location databases are commonly used in cyber security and anomaly detection, marketing and numerous other industries for converting IP addresses into physical location. IP2Loc provides a number of free and paid databases that offer varying degrees of precision and data set features.

On their website they give some examples of how to use their CSV or BIN databases with systems like MySQL. To this we must first convert an IPv4 address into its longform integer representation. This is technique is extremely common and widely used but the gist is:

```
IP Number = 16777216*w + 65536*x + 256*y + z
where
IP Address = w.x.y.z
```

Then we would take that number and perform a range query on the database like so:

```sql
SELECT (country_name, region_name, city_name, latitude, longitude, zip) FROM IP2LOC WHERE (ip_from  <= [SEARCH IP NO]) AND (ip_to >= [SEARCH IP NO]);
```

But as you might expect this query can take a long...long time to run especially if there are a lot of rows. In fact on my intial test it took 1.04 sec on average (with indexes) to return a result on a quad-core 16GB CentOS server. That is unbelievably, ridiculously, slow and is not suitable for production.

The code in this repository aims to improve on lookup performance so that IP2Location data can be used in real world systems where high throughput is neccesary.

Instead of using a traditional database, this system capitalizes on the nature of the data. This system builds a single contiguous array of keys and then performs a binary search over the keys to return a result. It takes on average 22 operations to find the data that we are looking for and returns this information in as little as 76 micro seconds. This is orders of magnitude faster. However it should be noted that in its current form, this service runs **directly** on Flask. This is **not** acceptable for production. I still need to wrap the whole thing in a production strength reverse-proxy like NGINX. Which I will do at some point in the future...Still after load testing I was able to get almost 2,000 queries per second through the service without it keeling over and dying.

To increase the ease of use this service has been wrapped as a Flask REST service. Unfortunately adding HTTP to our project causes our service to take quite a performance hit. After adding the REST wrapper query time was slowed to around 12ms per query, still much much better than before, but considerably slower than the 76 microseconds we were able to get without the interface. Additionally the entire service is packaged as an RPM using FPM (Effing Package Management) so that a user can simply use Yum to install the service. Finally the service is deployed as a Red Hat/Cent/Fedora system level service. This means you can bring it up using commands like:

```bash
systemctl ip2loc.service start
```

In order to get the service running you will need to add a python virutal environment to the working directory such that

```
IP2LocationService/venv/
```

is a valid path. You will want to install all the requirements listed in requirements.txt as they are neccesary for the service to run properly. Then you will need to download an IP2Location CSV based database. The free one [available here](http://lite.ip2location.com/database/ip-country-region-city-latitude-longitude-zipcode-timezone) is the easiest to get started with. Simply place the CSV in the working directory and start the service. The steps look like this:

1.) Clone this repo somewhere

2.) Install a virtual env using pip and the included requirements.txt file

3.) Download a Ip2Location database and place it in the same directory. Note that you may want to tailor the "named tuple" in ```search_ip_db.py``` to match the features present in your data. However it should work with the recommended DB out of the box.

Your directory structure should now look something like this:
```
	IP2LocationService/
		ip2loc.service
		make_links.sh
		remove_links.sh
		README.MD
		requirements.txt
		search_ip_db.py
		IP2LOCATIONDB.CSV
		/venv/
			all dependencies from requirements.txt
```

4.) Run FPM on the files in the directory with the following commands:
```bash
fpm -n ip2locService -s dir -t rpm --prefix /opt/ --directories /opt/IP2LocationService --after-install ./IP2LocationService/make_links.sh --before-remove ./IP2LocationService/remove_links.sh IP2LocationService
```

5.) Install the RPM that was just created by running
```bash
sudo yum localinstall IP2LocationService
```

6.) Start the service!
```bash
sudo systemctl ip2loc.service start
```

7.) Query the service and get results!
```bash
curl 127.0.0.1:5000/ip2location/getcoor/172.168.0.24

{"type": "success", "result": {"ip_from": 2896690944, "ip_to": 2896692991, "country_code": "US", "country_name": "United States", "region_name": "Virginia", "city_name": "Dulles", "latitude": 38.997708, "longitude": -77.433179, "zip_code": "20166", "time_zone": "-04:00"}}
```

This software is very much in pre-alpha so if you find any issues please let me know! 
