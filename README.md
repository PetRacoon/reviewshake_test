# reviewshake_test
Test Task for reviewshake

# What was done
- Created two spiders for: **yelp.com** and yelp.pt websites
- Two options available to both spiders: listing url and profile url
- 3 output processors: MongoDB, Postgresql, Json Lines

# How to run

- **install dependencies**

```
pip install -r requirements.txt
```

- **Configure storage processor**

Set **MONGO_URI** variable in settings.py file to store collected json to mongo db.
```
MONGO_URI = 'mongodb://0.0.0.0:27017'
```

set **SQL_DB_SETUP** mapping variable in setting.py to store collected json to sql table
```
SQL_DB_SETUP = {
   'dbname': "scrapy_items",
   'user': 'postgres',
   'password': 'passwd',
   'host': '0.0.0.0',
}
```
you also need already created database and tables in postgresql
```
CREATE DATABASE scrapy_items
CREATE TABLE companies (company_id varchar PRIMARY KEY, name varchar, phone varchar, category varchar,address varchar, city varchar);
CREATE TABLE reviews (review_id serial PRIMARY KEY, company_id  varchar, rating integer, review varchar, date varchar,FOREIGN KEY (company_id) REFERENCES companies (company_id));
```

If neither of those processors are configured output will be stored to output.js file.

- **run spider**

```
scrapy crawl yelp.com_spider --list_url="https://yelp.com/search/..." 
or 
scrapy crawl yelp.pt_spider --profile_url="http://yelp.pt/biz/..."
```

# Things to notice

1) I added ```UserAgent="TelegramBot"``` cause yelp blocks to much queries from same ip and with user-like userAgent.
I guess the best solution for this will be proxy and user-agent rotation. 

2) I decided to use json data block from html page to fill the data, cause css classes look's like dynamic ones, so i think they can change in some time.
3) Scrapy has very powerful pipeline processors, so i decided to use them for data storing.
4) Reviews pagination requires additional headers configuratio.
5) There are several issues with postgresql database writing:
  Because of async scrapy i have some issues with writing to database. The best solution here i guess is another "worker" which will store all collected data via some kind of Bulk.
6) P.S. I decided not to do additional work for storage module, cause i wanted to do this as fast as possible.
