def format_data(data):
    # Function to format data for display
    return [str(item).capitalize() for item in data]

def calculate_average(numbers):
    # Function to calculate the average of a list of numbers
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def filter_data(data, condition):
    # Function to filter data based on a condition
    return [item for item in data if condition(item)]