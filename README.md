# HCDS-EPD

## Data overview 
The English Prescribing Dataset (EPD) is a comprehensive resource detailing prescriptions issued by general practices in England and dispensed across the UK and Crown Dependencies. It is compiled and published monthly by the NHS Business Services Authority (NHSBSA) via the Open Data Portal and updated montly, the last update dates back to March 2025, the first records date back to January 2014.

For accessing the data, please visit : https://opendata.nhsbsa.net/dataset/english-prescribing-data-epd. Importantly no prior training needs to be done to gain access.

## Data Source and Collection:

The dataset is compiled from multiple NHSBSA data sources to ensure accuracy and consistency in prescription records. It is part of the Community prescribtion and dispensing datasets: https://opendata.nhsbsa.net/theme/about/community_prescribing_dispensing

## Licensing:

The EPD is released under the Open Government Licence 3.0 (United Kingdom), permitting free use, modification, and distribution of the data, however with propper attribution.


## Dataset Background & Fairness Considerations 

### When was the dataset created?

The dataset was first published in January 2014, and it has been updated monthly since.

### Preprocessing

1. Aggregation at the GP Practice/Cost Centre and item level
2. Standardization using British National Formulary (BNF) codes.
3. Calculation of: 
   - Total items 
     - the total number of times that the medicine, dressing or appliance
appeared on prescription forms that were prescribed and dispensed

   - Quantity and total quantity (Quantity × Total Items)

   - Net Ingredient Cost (NIC based on the Drug Tariff and manufacturer price)

   - Actual Cost (NIC minus average discounts + dispensing fees + rounding)

   - Average Daily Quantity (ADQ standardized to adult usage)

4. Exclusion of certain prescriptions (e.g., those from prisons, PGD-supplied, or not submitted to NHS Prescription Services).

### What are the protected attributes? 

1. Geographic region (STP, CCG, postal code) are protected to ensure that regional disparities are not disrupting the equal access or funding.
2. Type of medication prescribed (e.g., mental health related drugs, addiction) to ensure that community-level bias are avoided.
3. Practice name - not inherently protected, but might be used as a proxy to identify geographic and socioeconomic clusters.



