import numpy as np
import os
import pandas as pd


def check_database(database):
    '''
    Input: Pandas dataframe (Participant Database)
    Output: None - prints if it find duplicates
    '''

    for column in database.columns:
        if database[column].duplicated().sum():
            print(f'{column} - Duplicates were found in this database')
        else:
            print(f'{column} - Perfect')

    print()


def load_data(private_url, public_url):
    '''
    Input:
    -------
    private_url : contains user xslx filepath
    public_url  : contains past week partners filepath

    Output:
    -------
    database    : Pandas dataframe containing participant database
    register    : Pandas dataframe containing next week participant details
    weeks       : Contains past week participant details as pandas dataframe
    '''

    private_db = pd.ExcelFile(private_url)
    public_db = pd.ExcelFile(public_url)

    database = private_db.parse('Final')
    register = private_db.parse('Register')

    weeks = [public_db.parse(
        week) for week in public_db.sheet_names if week.startswith('Week_')]

    return (database, register, weeks)


def split_partners(week, database):
    '''
    Input:
    -------
    week           : Contain single week user data
    database       : Contains entire participant database

    Output:
    -------
    partner_list_1 : partner 1 names
    partner_list_2 : partner 2 names
    partner_status : status of the participants
    '''

    def def_partners_parse(partners): return [
        participant if participant is not np.nan else None for participant in partners]

    partner_list_1 = def_partners_parse(week.Partner_1.tolist())
    partner_list_2 = def_partners_parse(week.Partner_2.tolist())
    partner_status = (week.Status == 'Started')
    return (partner_list_1, partner_list_2), partner_status


def check_partners(*, p1, p2, db_names):
    '''
    p1  : particpant group 1 details
    p2  : particpant group 2 details
    db_names : entire participant details
    '''

    not_matched = []

    for a, b in zip(p1, p2):
        if (a is not None) and (a not in db_names):
            not_matched.append(a)
        if (b is not None) and (b not in db_names):
            not_matched.append(b)
    else:
        return None if len(not_matched) == 0 else not_matched


def parse_weeks(weeks, database):

    print('Checking for any errors in weeks:')

    user_dict = {}

    for (index, week) in enumerate(weeks, 1):

        (week_p1, week_p2), week_status = split_partners(week, database)
        verify = check_partners(p1=week_p1, p2=week_p2,
                                db_names=database['Full name'].tolist())
        print(f'Week_{index} : {verify}')

        user_dict['Week_'+str(index)] = {
            'week_p1': week_p1,
            'week_p2': week_p2,
            'week_status': week_status,
            'verify': verify
        }

    print()

    return user_dict


def generate_old_pair_json(user_dict, database):

    connections = {}
    def parse_number(
        participant): return database[database['Full name'] == participant]['WhatsApp Number'].tolist()[0]

    for week_name in user_dict.keys():
        week = user_dict[week_name]

        for p1, p2 in zip(week['week_p1'], week['week_p2']):
            if (p1 is None) or (p2 is None):
                continue

            p1_num = parse_number(p1)
            p2_num = parse_number(p2)

            dict_array = connections.get(p1_num, [])
            dict_array.append(p2_num)
            connections[p1_num] = dict_array

            dict_array = connections.get(p2_num, [])
            dict_array.append(p1_num)
            connections[p2_num] = dict_array

    return connections


def validate_and_parse_register(database, register):
    def retrieve_data(dataframe, column): return dataframe[column].tolist()

    db_email = retrieve_data(database, 'Email')
    db_number = retrieve_data(database, 'WhatsApp Number')
    register_email = retrieve_data(register, 'Email')
    register_number = retrieve_data(register, 'WhatsApp Number')
    new_connections = {}

    for user_email, user_number in zip(register_email, register_number):

        if user_email in db_email:
            usr_db = database[database['Email'] == user_email]
            new_connections[usr_db['Full name'].tolist()[0]] = [usr_db['Email'].tolist()[
                0], usr_db['WhatsApp Number'].tolist()[0]]

        elif user_number in db_number:
            usr_db = database[database['WhatsApp Number'] == user_number]
            new_connections[usr_db['Full name'].tolist()[0]] = [usr_db['Email'].tolist()[
                0], usr_db['WhatsApp Number'].tolist()[0]]

    return new_connections


def generate_random_pairs(connections, new_connections):
    random_pair = np.random.permutation(
        [partner for partner in new_connections.keys()]).reshape(-1, 2)

    for p1, p2 in random_pair:

        p1_num = new_connections[p1][1]
        p2_num = new_connections[p2][1]

        try:
            if p2_num in connections[p1_num]:
                return([])

            if p1_num in connections[p2_num]:
                return([])

        except:
            pass

    return random_pair


def create_output_dataframes(random_pair):

    # create_output_dataframes
    output = pd.DataFrame([], columns=['Partner_1', 'Partner_2',
                                       'P1_Number', 'P2_Number', 'P1_Email', 'P2_Email'])
    for p1, p2 in random_pair:

        p1_details, p2_details = new_connections[p1], new_connections[p2]

        usr_data = {
            # Partner Names
            'Partner_1': p1, 'Partner_2': p2,

            # Partner Whatsapp Numbers
            'P1_Number': p1_details[1],
            'P2_Number': p2_details[1],

            # Partner Email
            'P1_Email': p1_details[0],
            'P2_Email': p2_details[0]
        }

        output = output.append(usr_data, ignore_index=True)

    return output


private_url = 'assets/DSC ASEB Weekly Shuffle (Responses).xlsx'
public_url = 'assets/DSC ASEB Weekly Shuffle.xlsx'

database, register, weeks = load_data(private_url, public_url)

# print(f'Database : {database.columns}')
# print(f'Register : {register.columns}')
# print(f'weeks : {[week.columns for week in weeks]}')

print('Checking entire user database for any duplicates')
check_database(database)
user_dict = parse_weeks(weeks, database)
connections = generate_old_pair_json(user_dict, database)

print('Checking new register database for any duplicates')
check_database(register)

new_connections = validate_and_parse_register(database, register)
random_pair = []

while(len(random_pair) <= 0):
    random_pair = generate_random_pairs(connections, new_connections)

output = create_output_dataframes(random_pair)
print(output)
output.to_csv('Week_'+str(len(weeks)+1)+'.csv')
# with pd.ExcelWriter(public_url, engine = 'xlsxwriter') as writer:
# 	output.to_excel(writer, sheet_name = 'Week_'+str(len(weeks)+1))
