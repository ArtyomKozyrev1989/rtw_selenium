import pandas as pd
import random
import time
import re


class Employee:
    def __init__(self, id, paramedic, driver, trainee, dispatcher, chief, RM, JuHe, JuFa):
        self.id = id
        self.paramedic = paramedic
        self.driver = driver
        self.trainee = trainee
        self.dispatcher = dispatcher
        self.chief = chief
        self.RM = RM
        self.JuHe = JuHe
        self.JuFa = JuFa
        self.restrictions = []
        self.preferences = []
        self.time_preference = []

    def __str__(self):
        return '''
        id: {}
        paramedic: {}
        driver: {}
        trainee: {}
        dispatcher: {}
        chief: {}
        RM: {}
        JuHe: {}
        JuFa: {}
        restrictions: {}
        preferences: {}
        time_preference: {}
        '''.format(self.id, self.paramedic, self.driver,
                   self.trainee, self.dispatcher, self.chief,
                   self.RM, self.JuHe, self.JuFa, self.restrictions,
                   self.preferences, self.time_preference)

    def __repr__(self):
        return "Employee({})".format(self.id)

    def add_restriction(self, value):
        """ Some employees does not want to work with some other employees """
        self.restrictions.append(value)

    def remove_restriction(self, value):
        try:
            self.restrictions.remove(value)
        except ValueError:
            print("The value is not in restrictions list")

    def add_preference(self, value):
        """ Some employees would like to work with some other employees """
        self.preferences.append(value)

    def remove_preference(self, value):
        try:
            self.preferences.remove(value)
        except ValueError:
            print("The value is not in preferences list")

    def add_time_preference(self, start_time, end_time):
        """ Some employees can't work full day"""
        self.time_preference.append((start_time, end_time))


class EmployeeOp:

    def find_available_employees_list(file_name="available_employees.txt"):
        """The function is used to read list of available employees from txt file available_employees"""
        found_ids = []
        with open(file_name, 'r') as f:
            file_text = f.read()

        searched_pattern = '<div class="_instance _personInstance _volunteer" data-id=.+?">'
        found_lines = re.findall(searched_pattern, file_text)
        for line in found_lines:
            # line example: <div class="_instance _personInstance _volunteer" data-id="4781" data-name="Bдck Bettina">
            found_ids.append(line.split()[4].split("=")[1].strip('"'))
        return found_ids

    def create_employee_list(blacklist='blacklist.csv', preferences='wishlist.csv', memberlist='member_test1.csv'):
        restrictions_csv = pd.read_csv(blacklist)
        restrictions = []
        for line in restrictions_csv.values:
            #line exmple ['14069;5006']
            restrictions.append((list(line)[0].split(';')))

        preferences_csv = pd.read_csv(preferences)
        preferences = []
        for line in preferences_csv.values:
            # line example ['204397;307395;;'] and another example ['898365;;18:00;0:00']
            preferences.append((list(line)[0].split(';')))
        full_employees_csv = pd.read_csv(memberlist)  # this is full list of employees, not available employees
        available_employees_ids_list = EmployeeOp.find_available_employees_list()
        employees = []
        employees_trainees = []
        employees_with_retsrictions = []
        employee_with_time_restrictions = []
        for line in full_employees_csv.values:
            # line example ['366930;1;;;;;;;']
            if line[0].split(';')[0] in available_employees_ids_list:  # check if employee is available today
                employee = Employee(*list(line)[0].split(';'))
                for restr in restrictions:  # add restrictions to work with
                    # restr example #line ['14069', '5006']
                    if restr[0] == employee.id:
                        employee.add_restriction(restr[1])
                        employees_with_retsrictions.append(employee)
                    if restr[1] == employee.id:
                        employee.add_restriction(restr[0])
                        employees_with_retsrictions.append(employee)
                for wish in preferences:  # add desire to work with
                    # wish example ['898365', '333333333333', '18:00' , '0:00']
                    if wish[0] == employee.id:
                        if wish[1] != "":
                            employee.add_preference(wish[1])
                        if wish[2] != "":
                            employee.add_time_preference(wish[2], wish[3])
                            employee_with_time_restrictions.append(employee)
                if employee not in employee_with_time_restrictions:
                    # we'll add them in the end of list since we do not want them to be in rtw groups
                    employees.append(employee)
                if employee.trainee == "1":
                    employees_trainees.append(employee)
        random.shuffle(employees, random.random)
        random.shuffle(employees_trainees, random.random)
        random.shuffle(employees_with_retsrictions, random.random)
        employees = employees + employee_with_time_restrictions  # now add time restricted employees to the end of list
        return employees, employees_trainees, list(set(employees_with_retsrictions))

    def check_group_restrictions(group):
        for i in group:
            for j in group:
                if i.id in j.restrictions:
                    return False
        return True

    def driver_for_chief_group(chief, dispatcher1, dispatcher2, driver):
        if chief.id == "755":
            for i in employees:
                if driver is None and i.driver == "1" and i.restrictions != []:
                    driver = i
                    if EmployeeOp.check_group_restrictions([chief, dispatcher1, dispatcher2, driver]):
                        return driver
                    else:
                        driver = None
            for i in employees: # need the blocks since there could be drivers with no restrictions
                if driver is None and i.driver == "1":
                    driver = i
                    if EmployeeOp.check_group_restrictions([chief, dispatcher1, dispatcher2, driver]):
                        return driver
                    else:
                        driver = None
        else:
            return driver

    def remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, employee):
        if len(employees) > 0:
            if employee in employees:
                employees.remove(employee)
        if len(employees_trainees) > 0:
            if employee in employees_trainees:
                employees_trainees.remove(employee)
        if len(employees_with_retsrictions) > 0:
            if employee in employees_with_retsrictions:
                employees_with_retsrictions.remove(employee)

    def create_chief_group(employees, employees_trainees, employees_with_retsrictions):
        driver = None
        chief = None
        dispatcher1 = None
        dispatcher2 = None
        group_not_ready = True
        while group_not_ready:
            for i in employees:
                if chief is None and i.chief == "1":
                    chief = i
                    continue
                elif dispatcher1 is None and i.dispatcher == "1":
                    dispatcher1 = i
                    continue
                elif dispatcher2 is None and i.dispatcher == "1":
                    dispatcher2 = i
                    continue
                elif chief is not None and dispatcher1 is not None and dispatcher2 is not None:
                    if EmployeeOp.check_group_restrictions([chief, dispatcher1, dispatcher2]):
                        group_not_ready = False
                        break
                    else:
                        chief = None
                        dispatcher1 = None
                        dispatcher2 = None
                else:
                    continue
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, chief)
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, dispatcher1)
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, dispatcher2)
        # chief = Employee("755", "1", "", "", "", "1", "", "", "")
        # need to check what when 755 is chief
        driver = EmployeeOp.driver_for_chief_group(chief, dispatcher1, dispatcher2, driver)
        if driver:
            EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, driver)
            return [chief, dispatcher1, dispatcher2, driver]
        else:
            return [chief, dispatcher1, dispatcher2]

    def create_rtw_group(employees, employees_trainees, employees_with_retsrictions):
        driver = None
        pnd = None  # paramedic_not_driver
        trainee_or_pnd = None
        group_not_ready = True
        attempts_count_restrictions = 0
        while group_not_ready:
            for i in employees:
                if driver is None and i.driver == "1":
                    driver = i
                    continue
                elif pnd is None and i.paramedic == "1" and i.driver != "1":
                    pnd = i
                    continue
                elif trainee_or_pnd is None:
                    if len(employees_trainees) > 0:
                        trainee_or_pnd = employees_trainees[0]
                    else:
                        if i.paramedic == "1" and i.driver != "1":
                            trainee_or_pnd = i
                    continue
                elif driver is not None and pnd is not None and trainee_or_pnd is not None:
                    if EmployeeOp.check_group_restrictions([driver, pnd, trainee_or_pnd]):
                        group_not_ready = False
                        attempts_count_restrictions = 0
                        break
                    elif attempts_count_restrictions == 10:
                        group_not_ready = False
                        attempts_count_restrictions = 0
                        break
                    else:
                        driver = None
                        pnd = None
                        trainee_or_pnd = None
                        attempts_count_restrictions += 1
                else:
                    continue
            if group_not_ready:
                random.shuffle(employees, random.random)
                random.shuffle(employees_trainees, random.random)

        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, driver)
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, pnd)
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_with_retsrictions, trainee_or_pnd)
        return [driver, pnd, trainee_or_pnd]


if __name__ == '__main__':

    employees, employees_trainees, employees_with_retsrictions = EmployeeOp.create_employee_list()
    for i in employees:
        if i.preferences != []:
            print(str(i))
    print("Total employees: {}".format(len(employees)))
    print("Total trainees: {}".format(len(employees_trainees)))
    print("Total employee with restrictions: {}".format(len(employees_with_retsrictions)))
    with open("tests.txt", 'a') as f:
        f.write("Cycle ****************************************************************************")
    for i in EmployeeOp.create_chief_group(employees, employees_trainees, employees_with_retsrictions):
        print(i)
        with open("tests.txt",  'a') as f:
            f.write(str(i))

    for gr in range(0, 18):
        print("Group {}: \n".format(gr))
        with open("tests.txt",  'a') as f:
            f.write("Group {} *********************************************************: \n".format(gr))
        for i in EmployeeOp.create_rtw_group(employees, employees_trainees, employees_with_retsrictions):
            print(i)
            with open("tests.txt", 'a') as f:
                f.write(str(i))

    print("Total employees: {}".format(len(employees)))
    print("Total trainees: {}".format(len(employees_trainees)))
    print("Total employee with restrictions: {}".format(len(employees_with_retsrictions)))
    print("The calculations finished. The console will be closed in 60 seconds")
    time.sleep(5)

    for i in employees:
        print(str(i))
