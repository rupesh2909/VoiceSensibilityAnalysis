import sys
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from module1.customer_repository import (
    create_customer
)


CUSTOMERS = [

    ("Aarav Sharma", "RETAIL", "GOLD"),
    ("Aditi Mehta", "PREMIUM", "PLATINUM"),
    ("Arjun Kapoor", "RETAIL", "SILVER"),
    ("Ananya Singh", "RETAIL", "GOLD"),
    ("Rohan Verma", "SME", "GOLD"),
    ("Priya Nair", "PREMIUM", "PLATINUM"),
    ("Rahul Malhotra", "RETAIL", "STANDARD"),
    ("Sneha Iyer", "RETAIL", "SILVER"),
    ("Vikram Rao", "SME", "GOLD"),
    ("Neha Gupta", "PREMIUM", "PLATINUM"),

    ("Karan Patel", "RETAIL", "SILVER"),
    ("Pooja Shah", "RETAIL", "GOLD"),
    ("Aditya Joshi", "SME", "STANDARD"),
    ("Riya Agarwal", "PREMIUM", "GOLD"),
    ("Manish Tiwari", "RETAIL", "STANDARD"),
    ("Kavya Reddy", "RETAIL", "SILVER"),
    ("Siddharth Jain", "CORPORATE", "PLATINUM"),
    ("Meera Menon", "PREMIUM", "GOLD"),
    ("Nikhil Bansal", "RETAIL", "STANDARD"),
    ("Ishita Das", "RETAIL", "SILVER"),

    ("Varun Khanna", "SME", "GOLD"),
    ("Simran Kaur", "PREMIUM", "PLATINUM"),
    ("Abhishek Sinha", "RETAIL", "STANDARD"),
    ("Tanvi Kulkarni", "RETAIL", "GOLD"),
    ("Yash Thakur", "SME", "SILVER"),
    ("Shreya Kapoor", "PREMIUM", "GOLD"),
    ("Mohit Arora", "RETAIL", "STANDARD"),
    ("Nandini Rao", "RETAIL", "SILVER"),
    ("Akash Chawla", "CORPORATE", "PLATINUM"),
    ("Divya Iyer", "PREMIUM", "GOLD"),

    ("Saurabh Mishra", "RETAIL", "GOLD"),
    ("Muskan Jain", "RETAIL", "SILVER"),
    ("Harsh Vardhan", "SME", "STANDARD"),
    ("Sakshi Gupta", "PREMIUM", "PLATINUM"),
    ("Rajat Bhatia", "RETAIL", "GOLD"),
    ("Komal Sharma", "RETAIL", "STANDARD"),
    ("Aman Srivastava", "SME", "SILVER"),
    ("Bhavna Patel", "PREMIUM", "GOLD"),
    ("Gaurav Singhal", "CORPORATE", "PLATINUM"),
    ("Isha Khurana", "RETAIL", "SILVER"),

    ("Varsha Nair", "PREMIUM", "GOLD"),
    ("Dev Mehta", "RETAIL", "STANDARD"),
    ("Ritika Sharma", "SME", "GOLD"),
    ("Ankit Agarwal", "RETAIL", "SILVER"),
    ("Maya Iyer", "PREMIUM", "PLATINUM"),
    ("Deepak Verma", "CORPORATE", "GOLD"),
    ("Shalini Rao", "RETAIL", "STANDARD"),
    ("Kunal Shah", "SME", "SILVER"),
    ("Nisha Kapoor", "PREMIUM", "GOLD"),
    ("Rohit Malhotra", "RETAIL", "PLATINUM"),
]


def main():

    created = 0

    for name, segment, value in CUSTOMERS:

        customer_id = create_customer(
            customer_name=name,
            customer_segment=segment,
            customer_value=value
        )

        print(
            f"Created: {customer_id} | "
            f"{name} | "
            f"{segment} | "
            f"{value}"
        )

        created += 1

    print()
    print(
        f"Successfully created {created} customers."
    )


if __name__ == "__main__":

    main()