# ==========================================
# Title       : Weekly Shuffle Pattern Generator
# Repository  : https://github.com/DSC-ASEB/Weekly-Shuffle-Partner-Generator
# ==========================================

import sys
import numpy as np
import pandas as pd


def check_database(database):
    """
    It checks and prints the status if any duplicates exist by column wise in the input dataframe

    Parameters:
    -----
    Pandas dataframe (Participant Database)

    Returns:
    -----
    None
    """
    for column in database.columns:
        if database[column].duplicated().sum():
            print(f'{column} - Duplicates were found in this database')
        else:
            print(f'{column} - Perfect')

    print()


def load_data(private_filepath, public_filepath=None):
    """
    It will load the data from the input

    Parameters:
    -----
    private_filepath : contains user xslx filepath
    public_filepath  : contains past week partners filepath

    Returns:
    -----
    database    : Pandas dataframe containing participant database
    register    : Pandas dataframe containing next week participant details
    weeks       : Contains past week participant details as pandas dataframe
    """
    private_db = pd.ExcelFile(private_filepath)

    database = private_db.parse('Final')
    register = private_db.parse('Register')

    if public_filepath is not None:
        public_db = pd.ExcelFile(public_filepath)
        weeks = [public_db.parse(
            week) for week in public_db.sheet_names if week.startswith('Week_')]
        return (database, register, weeks)

    return (database, register, None)


def split_partners(week):
    """
    It splits both partner columns and status

    Parameters:
    -------
    week           : Contain single week user data

    Returns:
    -------
    partner_list_1 : partner 1 names
    partner_list_2 : partner 2 names
    partner_status : status of the participants
    """
    def def_partners_parse(partners):
        return [
            participant if participant is not np.nan else None for participant in partners]

    partner_list_1 = def_partners_parse(week.Partner_1.tolist())
    partner_list_2 = def_partners_parse(week.Partner_2.tolist())
    partner_status = (week.Status == 'Started')
    return (partner_list_1, partner_list_2), partner_status


def check_partners(*, p1, p2, db_names):
    """
    It checks whether partner names exist in the private database

    Parameters:
    -----
    p1  : particpant group 1 details
    p2  : particpant group 2 details
    db_names : entire participant details

    Returns:
    -----
    list of unmatched partner names to the database and None if every name matches to the database
    """
    not_matched = []

    for a, b in zip(p1, p2):
        if (a is not None) and (a not in db_names):
            not_matched.append(a)
        if (b is not None) and (b not in db_names):
            not_matched.append(b)

    return None if len(not_matched) == 0 else not_matched


def parse_weeks(weeks, database):
    """
    It creates dictionary holding important information regarding Week's partners and status

    Parameters:
    -----
    weeks    : list of week dataframes
    database : entire user dataframe

    Returns:
    -----
    user_dict: well structured weeks extracted data in dictionary datatype
    """
    print('Checking for any errors in weeks:')

    user_dict = {}

    for (index, week) in enumerate(weeks, 1):

        (week_p1, week_p2), week_status = split_partners(week)
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
    """
    It creates json of all the old weekly shuffle pairs

    Parameters:
    -----
    user_dict : well structured weeks extracted data in dictionary datatype
    database  : entire user dataframe

    Returns:
    -----
    connections : dictionary generated based on users number as key and value as old pair's (partner) number. [Phone Number]
    """
    connections = {}

    def parse_number(participant):
        return database[database['Full name'] == participant]['WhatsApp Number'].tolist()[0]

    for (week_number, week_name) in enumerate(user_dict.keys(), 1):
        week = user_dict[week_name]

        for p1, p2 in zip(week['week_p1'], week['week_p2']):

            exception = None

            if (p1 is None):
                exception = p2
            elif (p2 is None):
                exception = p1

            if (exception is not None):
                number = parse_number(exception)
                array = connections.get(number, [])
                array.append((number, week_number))
                connections[number] = array
            else:
                p1_num = parse_number(p1)
                p2_num = parse_number(p2)

                dict_array = connections.get(p1_num, [])
                dict_array.append((p2_num, week_number))
                connections[p1_num] = dict_array
                dict_array = connections.get(p2_num, [])
                dict_array.append((p1_num, week_number))
                connections[p2_num] = dict_array
    return connections


def validate_and_parse_register(database, register):
    """
    It verifies whether the register information exist in user database or not

    Parameters:
    -----
    database  : entire user dataframe
    register  : new week applicants dataframe

    Returns:
    -----
    new_connections : dictionary containing their names as keys and values as email and phone number.
    """
    def retrieve_data(dataframe, column):
        return dataframe[column].tolist()

    db_email = retrieve_data(database, 'Email')
    db_number = retrieve_data(database, 'WhatsApp Number')
    register_email = retrieve_data(register, 'Email')
    register_number = retrieve_data(register, 'WhatsApp Number')
    new_connections = {}
    present = True

    for user_email, user_number in zip(register_email, register_number):

        if user_email in db_email:
            usr_db = database[database['Email'] == user_email]
            new_connections[usr_db['Full name'].tolist()[0]] = [usr_db['Email'].tolist()[
                0], usr_db['WhatsApp Number'].tolist()[0]]

        elif user_number in db_number:
            usr_db = database[database['WhatsApp Number'] == user_number]
            new_connections[usr_db['Full name'].tolist()[0]] = [usr_db['Email'].tolist()[
                0], usr_db['WhatsApp Number'].tolist()[0]]
        else:
            print('[Error - Not Present - Database]')
            print(user_email, user_number)
            present = False
            print()

    return new_connections if present else None


def generate_random_pairs(new_connections, connections=None):
    """
    It generates a list of pairs using numpy's permutation function

    Parameters:
    -----
    connections     : contains past week's participants data
    new_connections : contains present week's particpants data

    Returns:
    -----
    list of random pairs generated
    """
    random_pairs = np.random.permutation(
        list(new_connections.keys())).reshape(-1, 2)

    if connections is None:
        return random_pairs

    for p1, p2 in random_pairs:

        p1_num = new_connections[p1][1]
        p2_num = new_connections[p2][1]

        if p2_num in connections.get(p1_num, []):
            return([])

        if p1_num in connections.get(p2_num, []):
            return([])

    return random_pairs


def create_output_dataframes(random_pairs, connections_new):
    """
    It generates a dataframe, so it can be converted to a csv file later on

    Parameters:
    -----
    random_pairs : list of randomly generated particpants data
    connections_new : dictionary holding register users data

    Returns:
    -----
    return_pd : dataframe containing participants name, email and phone number
    """
    return_pd = pd.DataFrame([], columns=['Partner_1', 'Partner_2',
                                          'P1_Number', 'P2_Number', 'P1_Email', 'P2_Email'])
    for p1, p2 in random_pairs:

        p1_details, p2_details = connections_new[p1], connections_new[p2]

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

        return_pd = return_pd.append(usr_data, ignore_index=True)

    return return_pd


def generate_inactive_and_active(old_pairs, week_no):
    """
    It generates a dictionary with active and inactive participants numbers.

    Parameters:
    -----
    old_pairs : It contains dictionary of participants with old pairs.
    week_no     : last week number

    Returns:
    -----
    dictionary with "Active" and "Inactive" as keys
    """
    print()
    compare_list = range(week_no-2, week_no+1)
    active, inactive = [], []
    for key in old_pairs.keys():
        if set(compare_list).issubset({value[1] for value in old_pairs[key]}):
            active.append(key)
        else:
            inactive.append(key)

    return {'Active': active, 'Inactive': inactive}


def output_active_inactive(db, jsnn):
    """
    It generates a Panda's DataFrames for active and inactive participants information.

    Parameters:
    -----
    db : It contains all user information
    jsnn : It contains generate_inactive_and_active() json

    Returns:
    -----
    Panda's DataFrames for active and inactive participants
    """
    def retrieve_number(number):
        return db[db['WhatsApp Number'] == number].iloc[0].tolist()
    active_list = [retrieve_number(usr) for usr in jsnn['Active']]
    inactive_list = [retrieve_number(usr) for usr in jsnn['Inactive']]

    return (pd.DataFrame(active_list, columns=['Name', 'Email', 'Number']),
            pd.DataFrame(inactive_list, columns=['Name', 'Email', 'Number']))


if __name__ == '__main__':

    if ((2 > len(sys.argv)) or (len(sys.argv) > 3)):
        print('Incorrect number of arguments')
        print('Usage: python run-script.py database.xlsx week_shuffle.xlsx')
        print('Usage: python run-script.py database.xlsx # if you are just using this tool for first time')
        sys.exit()

    if (len(sys.argv) == 3):

        private_url = sys.argv[1]
        public_url = sys.argv[2]

        database, register, weeks = load_data(private_url, public_url)

        print('Checking entire user database for any duplicates')
        check_database(database)
        user_dict = parse_weeks(weeks, database)
        connections = generate_old_pair_json(user_dict, database)

        print('Checking new register database for any duplicates')
        check_database(register)

        new_connections = validate_and_parse_register(database, register)

        if new_connections is None:
            print('\nCheck for errors in the register or database.')
            sys.exit()
        elif len(new_connections) % 2 != 0:
            print(
                '\nOdd number of participants exist in register sheet. Make it even to generate pairs.')
            sys.exit()

        random_pair = []

        while(len(random_pair) <= 0):
            print("[Reshuffling]")
            random_pair = generate_random_pairs(new_connections, connections)

        output = create_output_dataframes(random_pair, new_connections)
        print(output[['Partner_1', 'Partner_2']])
        output.to_csv('Week_'+str(len(weeks)+1)+'.csv')

        # Debug
        jsn = generate_inactive_and_active(connections, len(weeks))
        active_pd, inactive_pd = output_active_inactive(database, jsn)

        active_pd.to_csv('active_participants.csv', index=False)
        inactive_pd.to_csv('inactive_participants.csv', index=False)

    if (len(sys.argv) == 2):

        private_url = sys.argv[1]
        database, register, _ = load_data(private_url)

        print('Checking entire user database for any duplicates')
        check_database(database)

        print('Checking new register database for any duplicates')
        check_database(register)

        new_connections = validate_and_parse_register(database, register)

        if new_connections is None:
            print('\nCheck for errors in the register or database.')
            sys.exit()
        elif len(new_connections) % 2 != 0:
            print(
                '\nOdd number of participants exist in register sheet. Make it even to generate pairs.')
            sys.exit()

        random_pair = generate_random_pairs(new_connections)

        output = create_output_dataframes(random_pair, new_connections)
        print(output[['Partner_1', 'Partner_2']])
        output.to_csv('Week_1.csv')
        sys.exit()
