import pandas as pd
import random
import string
import os
from faker import Faker

# Initialize Faker and create a random seed for reproducibility
fake = Faker('en_GB')  # Set locale to UK for generating UK addresses
Faker.seed(0)
random.seed(0)

# Constants
num_records = 70007  # Set the number of records (1 million)
agents_count = 3132  # Number of agents to simulate
policy_types = ['Health', 'Life']
claim_statuses = ['Approved', 'Processing', 'Rejected']

# Function to generate custom IDs for each table with prefix and suffix
def generate_custom_id(table_prefix):
    # Generate 8 random digits
    digits = random.choices(string.digits, k=8)
    
    # Generate 2 random letters for the suffix
    suffix = random.choices(string.ascii_uppercase, k=2)
    
    # Combine prefix, digits, and suffix to form the ID
    return f"{table_prefix}{''.join(digits)}{''.join(suffix)}"

# Helper function to create random data
def create_prospect_data():
    return {
        'prospect_id': generate_custom_id("PR"),
        'name': fake.name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'created_at': fake.date_this_decade(),
        'status': random.choice(['Interested', 'Converted', 'Not Interested'])
    }

def create_customer_data(agent_ids, address_ids):
    agent_id = random.choice(agent_ids)
    address_id = random.choice(address_ids)
    customer = {
        'customer_id': generate_custom_id("CU"),
        'name': fake.name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'address_id': address_id,  # Store address_id instead of full address
        'agent_id': agent_id,
        'joined_date': fake.date_this_decade(),
        'status': random.choice(['Active', 'Inactive', 'Suspended'])
    }
    return customer

def create_address_data():
    return {
        'address_id': generate_custom_id("AD"),
        'street': fake.street_address(),
        'city': fake.city(),
        'county': fake.county(),
        'postcode': fake.postcode(),
        'country': 'United Kingdom'
    }

def create_policy_data(customer_ids):
    return {
        'policy_id': generate_custom_id("PO"),
        'customer_id': random.choice(customer_ids),
        'policy_type': random.choice(policy_types),
        'start_date': fake.date_this_decade(),
        'end_date': fake.date_this_decade(),
        'premium_amount': round(random.uniform(1000, 50000), 2),
        'status': random.choice(['Active', 'Expired', 'Cancelled'])
    }

def create_claim_data(policy_ids):
    return {
        'claim_id': generate_custom_id("CL"),
        'policy_id': random.choice(policy_ids),
        'claim_date': fake.date_this_decade(),
        'claim_amount': round(random.uniform(100, 20000), 2),
        'claim_status': random.choice(claim_statuses),
        'approved_amount': round(random.uniform(100, 15000), 2) if random.choice(claim_statuses) == 'Approved' else 0
    }

def create_agent_data():
    return {
        'agent_id': generate_custom_id("AG"),
        'agent_name': fake.name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'hire_date': fake.date_this_decade(),
        'commission_rate': round(random.uniform(0.05, 0.15), 2)
    }

def create_commission_data(agent_ids, policy_ids):
    return {
        'commission_id': generate_custom_id("CM"),
        'agent_id': random.choice(agent_ids),
        'policy_id': random.choice(policy_ids),
        'commission_amount': round(random.uniform(100, 5000), 2),
        'paid_date': fake.date_this_decade()
    }

def create_quote_data():
    return {
        'quote_id': generate_custom_id("QT"),
        'prospect_id': generate_custom_id("PR"),
        'quote_date': fake.date_this_decade(),
        'premium_amount': round(random.uniform(1000, 20000), 2),
        'valid_till': fake.date_this_decade(),
        'status': random.choice(['Issued', 'Accepted', 'Declined'])
    }

def create_sales_data():
    return {
        'sales_id': generate_custom_id("SA"),
        'agent_id': generate_custom_id("AG"),
        'customer_id': generate_custom_id("CU"),
        'sale_date': fake.date_this_decade(),
        'sale_amount': round(random.uniform(2000, 50000), 2),
        'status': random.choice(['Completed', 'Pending', 'Refunded'])
    }

# Create DataFrames to store all the data
def generate_data():
    agents = [create_agent_data() for _ in range(agents_count)]
    agent_df = pd.DataFrame(agents)

    # Create addresses (UK-specific)
    addresses = [create_address_data() for _ in range(num_records)]
    address_df = pd.DataFrame(addresses)

    # Create prospects
    prospects = [create_prospect_data() for _ in range(22347)]
    prospect_df = pd.DataFrame(prospects)

    # Create customers and link them to agents and addresses
    customer_ids = []
    address_ids = address_df['address_id'].tolist()  # List of address IDs
    for _ in range(num_records):
        customer_data = create_customer_data(agent_df['agent_id'].tolist(), address_ids)
        customer_ids.append(customer_data['customer_id'])
    customer_df = pd.DataFrame([create_customer_data(agent_df['agent_id'].tolist(), address_ids) for _ in range(num_records)])

    # Create policies
    policy_df = pd.DataFrame([create_policy_data(customer_df['customer_id'].tolist()) for _ in range(52407)])

    # Create claims
    claim_df = pd.DataFrame([create_claim_data(policy_df['policy_id'].tolist()) for _ in range(30143)])

    # Create commissions
    commission_df = pd.DataFrame([create_commission_data(agent_df['agent_id'].tolist(), policy_df['policy_id'].tolist()) for _ in range(22406)])

    # Create quotes
    quote_df = pd.DataFrame([create_quote_data() for _ in range(12043)])

    # Create sales data
    sales_df = pd.DataFrame([create_sales_data() for _ in range(11412)])

    return prospect_df, customer_df, address_df, policy_df, claim_df, agent_df, commission_df, quote_df, sales_df

# Generate the data
prospect_df, customer_df, address_df, policy_df, claim_df, agent_df, commission_df, quote_df, sales_df = generate_data()

# Create "syntheticData" subfolder if it doesn't exist
output_folder = 'syntheticData'
os.makedirs(output_folder, exist_ok=True)

# Save the data to CSV in the "syntheticData" subfolder
address_df.to_csv(os.path.join(output_folder, 'addresses.csv'), index=False)  # Save the address table first
prospect_df.to_csv(os.path.join(output_folder, 'prospects.csv'), index=False)
customer_df.to_csv(os.path.join(output_folder, 'customers.csv'), index=False)
policy_df.to_csv(os.path.join(output_folder, 'policies.csv'), index=False)
claim_df.to_csv(os.path.join(output_folder, 'claims.csv'), index=False)
agent_df.to_csv(os.path.join(output_folder, 'agents.csv'), index=False)
commission_df.to_csv(os.path.join(output_folder, 'commissions.csv'), index=False)
quote_df.to_csv(os.path.join(output_folder, 'quotes.csv'), index=False)
sales_df.to_csv(os.path.join(output_folder, 'sales.csv'), index=False)

print("Data generation complete! Files are saved in the 'syntheticData' folder.")
