####################################################################################################
# Database, Initialize some data manually for testing the system

"""
In-memory database for now.
Later we can replace with real database.

Preferred Databases based in each category:
    - Graph Database:         ( Neo4j --> Kuzu )
    - Vector Database:        ( Milvus | Weaviate | Qdrant | Pinecone )
    - Relational Database:    ( PostgreSQL )
"""

from APP.Classes import Student

students=[
    Student("Ahmad Gaffar",27,"01010101334","ahmadgaffar@outlook.com",1,70,10,90),
    Student("Amir Abdulmaaboud", 38, "01001111700", "amir_coffe@yahoo.com", 2, 80, 6, 70),
    Student("Karim Suliman", 32, "01024026326", "karim_suliman@gmail.com", 3, 60, 7, 80),
    Student("Muhammad Abdulhamid", 27, "01001235667", "muhammad13Abdulhamid@gmail.com", 4, 70, 2, 100),
    Student("Mostafa Mohsen", 25, "01009031990", "mostafa_mohsen12@outlook.com", 5, 80, 9, 90),
    Student("Omar El-Ashry", 28, "01001212543", "omar_ashry@outlook.com", 6, 80, 5, 70),
    Student("Ali Ibrahim", 27, "01002412693", "ali_ibrahim128@outlook.com", 7, 90, 3, 00),
    Student("Abdullah Mansor", 30, "01000660873", "abdullah_mansor@gmail.com", 8, 70, 2, 70),
    Student("Magdy Muhammad", 29, "01001718192", "magdy76muhammed@gmail.com", 9, 100, 1, 60),
    Student("Ibrahim Tork", 29, "01002359870", "ibrahimtork@gmail.com", 10, 50, 1, 80),
    Student("Dagher Abdulnasser", 30, "01096026732", "dagher77@gmail.com", 5, 70, 8, 90),
    Student("Saaed Mahmoud", 28, "01011443736", "saaedMahmoud@gmail.com", 10, 100, 9, 30),
]

####################################################################################################