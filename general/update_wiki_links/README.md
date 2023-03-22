# Create wiki links API update 

This script aims to help us update a large number of default wiki links.
However, it also creates an API file, which you can use to customize wiki links.

The Python script for updating wiki links is `create_wiki_links_api_update.py`

You will need the following.
1. Python 3
2. Pystache module
3. Input files

Input files
1. Mustache template to create a Liquibase file
2. Configuration view properties for the wiki
3. Links to update in TSV format

Output files
1. A properties object file to update the API to test properties
2. A Liquibase file to update the database


---

## Input files

You must supply the input files, except the Mustache template, which you can customize.

### Mustache template

This file is in the base folder with the Python script.
It should contain sections for each operation (updates, creates, deletes)
The file name is `wiki_links_liquibase.mustache`

---

### Current properties object

The API stores the default wiki links for Configuration view in the API.
To obtain the current properties, make a GET request to the [SystemPropertiesResource](https://wiki.abiquo.com/api/latest/SystemPropertiesResource.html).
It is best to obtain the properties just for the `client.wiki` component.

You can use the following cURL command, with appropriate values for your environment:
```
 curl -XGET "https://mjsabiquo.lab.abiquo.com/api/config/properties?component=client.wiki" \                                   
 -H "Accept: application/vnd.abiquo.systemproperties+json; version=6.1" \
 -u admin:xabiquo -k \    
 
```

Save the results in a file at: `input_files/v61_wiki_properties_client.json`
The file names are currently hard coded in the script because hopefully we won't need to do this process often!

Here is an extract from the start of the data object.

```
{
  "links": [],
  "collection": [
    {
      "id": 259,
      "name": "client.wiki.allocation.datacenter",
      "value": "https://wiki.abiquo.com/display/doc/Allocation+Rules#AllocationRules-DatacenterRulesManagement",
      "description": "datacenter rules wiki",
      "links": [
        {
          "title": "client.wiki.allocation.datacenter",
          "rel": "edit",
          "type": "application/vnd.abiquo.systemproperty+json",
          "href": "https://mjsabiquo.lab.abiquo.com:443/api/config/properties/259"
        }
      ]
    },
    {
      "id": 258,
      ...
 ```

---

### Links to update in TSV format

Create a spreadsheet with the links to change, and include the following columns.

```operation   wikiLinkKey wikiLinkLabel currentLink newLink```

The mandatory columns are the *operation* to perform, the *property ID* (which is the wiki link key), and the *new link* value.
The supported operations are:
* CREATE
* UPDATE
* DELETE

Export the spreadsheet as a TSV file, which should look as follows.

#### TSV file format

| operation |	wikiLinkKey |	wikiLinkLabel |	currentLink |	newLink |
|:----------|:--------------|:----------------|:------------|:----------|
| UPDATE	| client.wiki.infra.createDatacenter |	Create datacenter  | `https://wiki.abiquo.com/display/doc/Manage+Datacenters` |	`https://wiki.abiquo.com/display/doc/Create+a+datacenter` |
| CREATE	| client.wiki.network.managePublicQoS |	Manage Public QoS |	 | `https://abiquo.atlassian.net/wiki/display/doc/Limit+bandwidth+of+Public+IPs` |
| DELETE    |client.wiki.infra.editRemoteService |	Edit remote service | |	`https://wiki.abiquo.com/display/doc/ModifyRemoteServices` |	


Save your TSV file at `input_files/wiki_links_table_YYYY-MM-DD.tsv`
For example `input_files/wiki_links_table_2023-03-21.tsv`

The file name is currently hard coded in the script with the system date for today. 

---

## Running the script

When you have the input files in the correct location, you can run the script with Python 3:
```python create_wiki_links_api_update.py```

It may print out some debugging stuff but it doesn't do any logging or exception handling or anything useful like that.
It should create the output files as described below.

---


## Output files

You can use the following output files to update the wiki links in Abiquo. 
The properties object for API update is only suitable for testing or for loading custom links.
The Liquibase file is suitable for updating the default links in the database.


### Properties object for API update

One output is a file containing a properties object that you can use to update the Abiquo API to test your new wiki links.
You can find this file at `output_files/wiki_links_api_file_YYYY_MM_DD.txt`.
The script uses today's date and the rest of the file name is hard coded in the script.

This is a raw JSON file, so you may want to parse it, for example, with a command like this one (assuming you have JQ):
```
cat wiki_links_api_file_2023-03-21.txt | jq . > wiki_links_api_file_formatted_2023-03-21.json
```
Note that the format of this object is not the same as the format of the object returned by the GET request above. Sigh.
Here is an example of the start of a properties object file.

```

{
  "links": [],
  "collection": [
    {
      "id": 259,
      "name": "client.wiki.allocation.datacenter",
      "value": "https://abiquo.atlassian.net/wiki/spaces/doc/pages/311370944/Allocation+rules",
      "description": "datacenter rules wiki",
      "links": [
        {
          "title": "client.wiki.allocation.datacenter",
          "rel": "edit",
          "type": "application/vnd.abiquo.systemproperty+json",
          "href": "https://mjsabiquo.lab.abiquo.com:443/api/config/properties/259"
        }
      ],
      "__property": "client.wiki.allocation.datacenter"
    },
    {
      "id": 258,
      ...
 ```


---

#### Update your API with the wiki links for testing

To update your Abiquo with your new wiki links via the API, you can use a cURL command like this one to read in the properties object file:
```
 curl -XPUT "https://mjsabiquo.lab.abiquo.com/api/config/properties?component=client.wiki" \                                   
 -H "Accept: application/vnd.abiquo.systemproperties+json; version=6.1" \
 -H "Content-Type: application/vnd.abiquo.systemproperties+json; version=6.1" \
 -u admin:xabiquo -k \    
 -d @output_files/wiki_links_api_file_2023-03-21.json
```

*Note: this command does something strange to the More info on deploy link, so only use it on a test system*

---

### Liquibase file

The Liquibase file will contain the information to update an Abiquo database with the wiki links.

You can find this file at `output_files/wiki_links_api_file_YYYY_MM_DD.txt`.
The script uses today's date and the rest of the file name is hard coded in the script.

The content of the Liquibase file will remain a mystery.
You can give this content to your Dev team, so they can update the database.

---
