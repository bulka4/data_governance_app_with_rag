This is a new version of the code from the `metadata_extraction` folder. This version:
    - Uses Python
    - Classes (`dataclass`) to store data about objects such as tables, columns and scripts
    - Uses an interface `MetadataExtractor` to define what methods all the classes for extracting metadata, for different SQL servers (MySQL, MS SQL, etc.), should have

This code was not tested yet, it is just an initial draft.