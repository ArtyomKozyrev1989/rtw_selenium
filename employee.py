import pandas as pd
import random
import copy
import re
import time
import logging

logt = time.localtime()

logging.basicConfig(
    filename='logging_rtw_gr_{}{}{}.log'.format(logt.tm_year,
                                                str(logt.tm_mon).rjust(2, "0"),
                                                str(logt.tm_mday).rjust(2, "0")),
    level=logging.WARNING, format='%(asctime)s %(message)s')

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
        self.type = self.define_employee_type()

    def define_employee_type(self):
        if self.driver == "1":
            return "driver"
        elif self.driver != "1" and self.paramedic == "1":
            return "pnd"
        elif self.trainee == "1":
            return "trainee"
        else:
            return "other"

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

    def find_if_restricted(team, employee):
        """ check if employee can work with other team member based on personal blacklist restrictions"""
        for i in team:
            if (employee.id in i.restrictions) or (i.id in employee.restrictions):
                return True
        return False

    def check_normal_group(group, employees):
        """check if group has normal number of drivers, pnd, trainee"""
        driver = 0
        pnd = 0
        trainee = 0
        tempgroup = copy.copy(group)
        for e in group:
            if e.driver == "1":
                driver += 1
                if driver > 1:
                    tempgroup.remove(e)
                    driver -= 1
                    continue
            elif e.driver != "1" and e.trainee != "1":
                pnd += 1
                if pnd > 1:
                    tempgroup.remove(e)
                    pnd -= 1
                    continue
            elif e.trainee == "1": # if no trainees left as a result of the operation another pnd will be added to group
                trainee += 1
                if trainee > 1:
                    tempgroup.remove(e)
                    trainee -= 1
                    continue
            else:
                pass
        group = tempgroup # I know that it is shallow copy
        if driver == 0:
            group.append(EmployeeOp.find_new_driver(group, employees))
        if pnd == 0:
            group.append(EmployeeOp.find_new_pnd(group, employees))
        if trainee == 0:
            group.append(EmployeeOp.find_new_trainee(group, employees))
        return group

    def create_dream_group(employees, employees_trainees_ids, employee_trainees, employee_with_pr):
        second_member_id = employee_with_pr.preferences[0]
        second_member = None
        third_member_id = None
        third_member = None
        for i in employees:
            if i.id == second_member_id:
                second_member = i # was discussed to ignore situation when if A in B blacklist
                break
        else:
            if employee_with_pr.type == "driver":
                second_member = EmployeeOp.find_new_pnd([employee_with_pr], employees)
            if employee_with_pr.type == "pnd":
                second_member = EmployeeOp.find_new_driver([employee_with_pr], employees)
            if employee_with_pr.type == "trainee":
                second_member = EmployeeOp.find_new_driver([employee_with_pr], employees)
        if employees_trainees_ids and employee_with_pr.id not in employees_trainees_ids and second_member.id not in employees_trainees_ids:
            if second_member.preferences:
                if second_member.preferences[0] in employees_trainees_ids:
                    third_member_id = second_member.preferences[0]
                    for i in employees:
                        if i.id == third_member_id and not EmployeeOp.find_if_restricted(
                                [second_member, employee_with_pr], i):
                            third_member = i
                            break
                else:
                    third_member = EmployeeOp.find_new_trainee([second_member, employee_with_pr], employees)
            else:
                third_member = EmployeeOp.find_new_trainee([second_member, employee_with_pr], employees)
        else:
            if employee_with_pr.driver != 1 and second_member.driver != 1:
                third_member = EmployeeOp.find_new_pnd([second_member, employee_with_pr], employees)
            else:
                third_member = EmployeeOp.find_new_driver([second_member, employee_with_pr], employees)

        result = EmployeeOp.check_normal_group([employee_with_pr, second_member, third_member], employees)
        for emp in result:
            EmployeeOp.remove_employee_from_groups(employees, employee_trainees, employees_trainees_ids, emp)
        return result


    def find_new_driver(group, employees):
        for i in employees:
            if i.type == "driver" and not EmployeeOp.find_if_restricted(group, i):
                return i
        else:
            return None

    def find_new_pnd(group, employees):
        for i in employees:
            if i.type == "pnd" and not EmployeeOp.find_if_restricted(group, i):
                return i
        else:
            return None

    def find_new_trainee(group, employees):
        for i in employees:
            if i.type == "trainee" and not EmployeeOp.find_if_restricted(group, i):
                return i
        else:
            EmployeeOp.find_new_pnd(group, employees) # if was not able to find trainee for group

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
        available_employees_ids_list = EmployeeOp.find_available_employees_list() # for the day
        employees = []
        employees_trainees = []
        employees_trainees_ids = []
        employees_with_retsrictions = []
        employees_with_preferences = []
        employees_with_time_restrictions = []
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
                            employees_with_preferences.append(employee)
                        if wish[2] != "":
                            employee.add_time_preference(wish[2], wish[3])
                            employees_with_time_restrictions.append(employee)
                if employee not in employees_with_time_restrictions:
                    # we'll add them in the end of list since we do not want them to be in rtw groups
                    employees.append(employee)
                if employee.trainee == "1":
                    employees_trainees_ids.append(employee.id)
                    employees_trainees.append(employee)
        random.shuffle(employees, random.random)
        random.shuffle(employees_trainees, random.random)
        random.shuffle(employees_with_retsrictions, random.random)
        employees = employees + employees_with_time_restrictions  # now add time restricted employees to the end of list
        for i in employees_with_preferences: # if employee have time preferences - remove it
            if i in employees_with_time_restrictions:
                employees_with_preferences.remove(i)
        return employees, employees_trainees, employees_with_preferences,\
               list(set(employees_with_retsrictions)),  employees_trainees_ids

    def choose_chief_and_driver(employees, employees_trainees, employees_trainees_ids):
        """ Find chief and driver if chief need driver """
        chief = None
        driver = None
        for e in employees:
            if e.chief == "1":
                chief = e
                break
        if chief.id == "755":
            for e in employees:
                if e.id == '278349':
                    driver = e
                    break
            if not driver:
                for e in employees:
                    if e.driver == "1" and e not in chief.restrictions and chief not in e.restrictions:
                        driver = e
                        break
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_trainees_ids, chief)
        if driver:
            EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_trainees_ids, driver)
        return [chief, driver]

    def choose_dispatcher(employees, employees_trainees, employees_trainees_ids):
        """ Find dispatchers"""
        dispatcher = None
        for e in employees:
            if e.dispatcher == "1":
                dispatcher = e
                EmployeeOp.remove_employee_from_groups(employees, employees_trainees,
                                                       employees_trainees_ids, dispatcher)
                return dispatcher

    def remove_employee_from_groups(employees, employees_trainees, employees_trainees_ids, employee):
        if len(employees) > 0 and employee:
            try:
                employees.remove(employee)
            except Exception as ex:
                print(ex)
        if len(employees_trainees) > 0:
            if employee in employees_trainees:
                employees_trainees.remove(employee)
        if len(employees_trainees_ids) > 0:
            if employee.id in employees_trainees_ids:
                employees_trainees_ids.remove(employee.id)



    def check_group_restrictions(group):
        for i in group:
            for j in group:
                if i.id in j.restrictions:
                    return False
        return True

    def create_rtw_group(employees, employees_trainees, employees_trainees_ids):
        if len(employees) < 3:
            print("Can't create RTW, employees number < 3")
            return employees
        driver = None
        pnd = None  # paramedic_not_driver
        trainee_or_pnd = None
        group_not_ready = True
        attempts_count_restrictions = 0
        full_stop = 1
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
                        logging.warning("WAS NOT ABLE TO CREATE GROUP ACCORDING TO RULES!!!")
                        logging.warning("{}".format([driver, pnd, trainee_or_pnd]))
                        break
                    else:
                        driver = None
                        pnd = None
                        trainee_or_pnd = None
                        attempts_count_restrictions += 1
                else:
                    continue
            if group_not_ready:
                driver = None
                pnd = None
                trainee_or_pnd = None
                random.shuffle(employees, random.random)
                random.shuffle(employees_trainees, random.random)
                full_stop += 1
                if full_stop == 5:
                    break

        if driver == pnd or driver == trainee_or_pnd or trainee_or_pnd == pnd:
            logging.warning("ABNORMAL SITUATION ATTENTION!!!")
            logging.warning("{}".format([driver, pnd, trainee_or_pnd]))

        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_trainees_ids, driver)
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_trainees_ids, pnd)
        EmployeeOp.remove_employee_from_groups(employees, employees_trainees, employees_trainees_ids, trainee_or_pnd)
        return [driver, pnd, trainee_or_pnd]


if __name__ == '__main__':
    (employees, employees_trainees, employees_with_preferences,
     employees_with_retsrictions, employees_trainees_ids) = EmployeeOp.create_employee_list()

    with open("result_{}{}{}.txt".format(
            logt.tm_year, str(logt.tm_mon).rjust(2, "0"), str(logt.tm_mday).rjust(2, "0")), 'a') as f:

        print("Available employees {} ".format(len(employees)))
        f.write("Available employees {} ".format(len(employees)) + "\n")
        # create chief group:
        chief_gr = EmployeeOp.choose_chief_and_driver(employees, employees_trainees, employees_trainees_ids)
        print("Chief group {}".format(chief_gr))
        f.write("Chief group {}".format(chief_gr) + "\n")
        for i in chief_gr:
            if i:
                print(i)
                f.write(str(i) + "\n")
        print("Available employees {} ".format(len(employees)))
        f.write("Available employees {} ".format(len(employees)) + "\n")

        dispatcher1 = EmployeeOp.choose_dispatcher(employees, employees_trainees, employees_trainees_ids)
        dispatcher2 = EmployeeOp.choose_dispatcher(employees, employees_trainees, employees_trainees_ids)

        print("Dispacther1 {}".format(dispatcher1))
        f.write("Dispacther1 {}".format(dispatcher1) + "\n")
        print("Dispacther2 {}".format(dispatcher2))
        f.write("Dispacther2 {}".format(dispatcher2) + "\n")
        print("Available employees {} ".format(len(employees)))
        f.write("Available employees {} ".format(len(employees)) + "\n")

        dream_groups = []
        for i in employees_with_preferences:
            if i in employees:  # it could be removed in one of previous steps
                group = EmployeeOp.create_dream_group(employees, employees_trainees_ids, employees_trainees, i)
                dream_groups.append(group)

        gr_n = 1
        for gr in dream_groups:
            print("Dream group # {}".format(gr_n))
            f.write("Dream group # {}".format(gr_n) + "\n")
            for i in gr:
                print(i)
                f.write(str(i) + "\n")
            gr_n += 1

        print("Available employees {} ".format(len(employees)))
        f.write("Available employees {} ".format(len(employees)) + "\n")

        # create normal groups:
        for i in range(1, 30 - gr_n):
            print("ORDINARY GROUP # {}".format(i))
            f.write("ORDINARY GROUP # {}".format(i) + "\n")
            ord_gr = EmployeeOp.create_rtw_group(employees, employees_trainees, employees_trainees_ids)
            print(ord_gr)
            f.write(str(ord_gr) + "\n")
            for i in ord_gr:
                print(i)
                f.write(str(i) + "\n")
            print("Available employees {} ".format(len(employees)))
            f.write("Available employees {} ".format(len(employees)))

        print("ALL who left")
        f.write("ALL who left" + "\n")
        for i in employees:
            f.write(str(i) + "\n")
            print(str(i))
    print("work is done!")
    time.sleep(20)
