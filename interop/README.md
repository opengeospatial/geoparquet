## About

This folder is the core of the actual interoperability experiment. It will have a section for each participant in the experiment, where we share the
results of imports and exports of various data sets. Each participant should import the reference data by any means necessary, and then export it into
all the different formats they support. They should then try to import each export from every other participant, and report on the success of each one.

## Reference Data

We'll be using Natural Earth data, since its global scale can help show places where geometry <-> geography may go awry. 

To start we'll use: https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_1_states_provinces.zip

TODO: Translate from shapefile to provide as different formats.

TODO: Add more datasets here.

## Participant Data

### BigQuery

#### Export Data

| **Data Type**             | **Link NE Admin 1** | **Notes** |
|---------------------------|---------------------|-----------|
| CSV w/ GeoJSON geometries |                     |           |
| CSV w/ WKT                |                     |           |
| CSV w/ WKB                |                     |           |
| CSV w/ EWKT               |                     |           |
| CSV w/ EWKB               |                     |           |
| GeoJSON                   |                     |           |
| Avro                      |                     |           |
| Parquet                   |                     |           |

#### Import Status

Enter 'Success' if every dataset works perfectly, 'N/A' if the provider does not export to the format, and 'Nope' with a brief note of what 
went wrong with any of the datasets. Use the space below the table to explain anything in more details.

|                           | **Oracle** | **BigQuery** | **Redshift** |
|---------------------------|------------|--------------|--------------|
| **Data Type**             |            |              |              |
| CSV w/ GeoJSON geometries |            |              |              |
| CSV w/ WKT                |            |              |              |
| CSV w/ WKB                |            |              |              |
| CSV w/ EWKT               |            |              |              |
| CSV w/ EWKB               |            |              |              |
| GeoJSON                   |            |              |              |
| Avro                      |            |              |              |
| Parquet                   |            |              |              |

### Snowflake

#### Export Data

| **Data Type**             | **Link NE Admin 1** | **Notes** |
|---------------------------|---------------------|-----------|
| CSV w/ GeoJSON geometries |                     |           |
| CSV w/ WKT                |                     |           |
| CSV w/ WKB                |                     |           |
| CSV w/ EWKT               |                     |           |
| CSV w/ EWKB               |                     |           |
| GeoJSON                   |                     |           |
| Avro                      |                     |           |
| Parquet                   |                     |           |

#### Import Status

Enter 'Success' if every dataset works perfectly, 'N/A' if the provider does not export to the format, and 'Nope' with a brief note of what 
went wrong with any of the datasets. Use the space below the table to explain anything in more details.

|                           | **Oracle** | **BigQuery** | **Redshift** |
|---------------------------|------------|--------------|--------------|
| **Data Type**             |            |              |              |
| CSV w/ GeoJSON geometries |            |              |              |
| CSV w/ WKT                |            |              |              |
| CSV w/ WKB                |            |              |              |
| CSV w/ EWKT               |            |              |              |
| CSV w/ EWKB               |            |              |              |
| GeoJSON                   |            |              |              |
| Avro                      |            |              |              |
| Parquet                   |            |              |              |

### Oracle

#### Export Data

| **Data Type**             | **Link NE Admin 1** | **Notes** |
|---------------------------|---------------------|-----------|
| CSV w/ GeoJSON geometries |                     |           |
| CSV w/ WKT                |                     |           |
| CSV w/ WKB                |                     |           |
| CSV w/ EWKT               |                     |           |
| CSV w/ EWKB               |                     |           |
| GeoJSON                   |                     |           |
| Avro                      |                     |           |
| Parquet                   |                     |           |

#### Import Status

Enter 'Success' if every dataset works perfectly, 'N/A' if the provider does not export to the format, and 'Nope' with a brief note of what 
went wrong with any of the datasets. Use the space below the table to explain anything in more details.

|                           | **Oracle** | **BigQuery** | **Redshift** |
|---------------------------|------------|--------------|--------------|
| **Data Type**             |            |              |              |
| CSV w/ GeoJSON geometries |            |              |              |
| CSV w/ WKT                |            |              |              |
| CSV w/ WKB                |            |              |              |
| CSV w/ EWKT               |            |              |              |
| CSV w/ EWKB               |            |              |              |
| GeoJSON                   |            |              |              |
| Avro                      |            |              |              |
| Parquet                   |            |              |              |

### Redshift

#### Export Data

| **Data Type**             | **Link NE Admin 1** | **Notes** |
|---------------------------|---------------------|-----------|
| CSV w/ GeoJSON geometries |                     |           |
| CSV w/ WKT                |                     |           |
| CSV w/ WKB                |                     |           |
| CSV w/ EWKT               |                     |           |
| CSV w/ EWKB               |                     |           |
| GeoJSON                   |                     |           |
| Avro                      |                     |           |
| Parquet                   |                     |           |

#### Import Status

Enter 'Success' if every dataset works perfectly, 'N/A' if the provider does not export to the format, and 'Nope' with a brief note of what 
went wrong with any of the datasets. Use the space below the table to explain anything in more details.

|                           | **Oracle** | **BigQuery** | **Redshift** |
|---------------------------|------------|--------------|--------------|
| **Data Type**             |            |              |              |
| CSV w/ GeoJSON geometries |            |              |              |
| CSV w/ WKT                |            |              |              |
| CSV w/ WKB                |            |              |              |
| CSV w/ EWKT               |            |              |              |
| CSV w/ EWKB               |            |              |              |
| GeoJSON                   |            |              |              |
| Avro                      |            |              |              |
| Parquet                   |            |              |              |
