import ast
import collections
import matplotlib.pyplot as plt
import datetime

def parse_output_file(filename):
    class_names = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and line.startswith('('):
                try:
                    # Use eval with safe globals to handle datetime
                    safe_globals = {
                        '__builtins__': {},
                        'datetime': datetime,
                        'timezone': datetime.timezone,
                    }
                    data = eval(line, safe_globals)
                    # The last element is the data_dict
                    data_dict = data[-1]
                    detections = data_dict.get('detections', [])
                    for detection in detections:
                        class_name = detection.get('class_name')
                        if class_name:
                            class_names.append(class_name)
                except Exception as e:
                    print(f"Error parsing line: {line[:100]}... Error: {e}")
                    continue
    return class_names

def create_histogram(class_names, output_file='histogram.png'):
    # Count frequencies
    counter = collections.Counter(class_names)
    
    # Prepare data for plotting
    labels = list(counter.keys())
    counts = list(counter.values())
    
    # Create histogram
    plt.figure(figsize=(10, 6))
    plt.bar(labels, counts, color='skyblue')
    plt.xlabel('Class Name')
    plt.ylabel('Frequency')
    plt.title('Histogram of Class Names in Detections')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(output_file)
    print(f"Histogram saved to {output_file}")
    
    # Optionally show the plot (comment out if not needed)
    # plt.show()

if __name__ == "__main__":
    filename = "output.txt"
    class_names = parse_output_file(filename)
    create_histogram(class_names)