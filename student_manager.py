async def name_validation(name):
    if len(name) < 3:
        return False
    
    for ch in name:
        if not ch.isalpha():
            return False
    
    return True

async def surname_validation(surname):
    if len(surname) < 3:
        return False
    
    for ch in surname:
        if not ch.isalpha():
            return False

    return True

async def age_validation(age):
    try:
        age = int(age)
        if age < 7:
            return False
        
        return True
    
    except:
        return False

async def phone_validation(phone_number):
    number = '+0123456789'
    for ch in phone_number:
        if ch not in number:
            return False
    if phone_number[0] == '+' and len(phone_number) < 12 or phone_number[0] != '+' and len(phone_number) < 9:
        return False
    
    return True
