import sys
import os
import json
import pandas as pd
import subprocess

import platform
isWindows = platform.system() == 'Windows'

root_folder = os.path.join(os.path.expanduser("~"), "git", "biologics-research-helix-wrapper-api")

def process_fasta_file(fasta_file_path):
    """
    Processes a FASTA file and extracts each sequence as an element of a list.
    
    Parameters:
    fasta_file_path (str): The path to the FASTA file.
    
    Returns:
    list[tuple]: A list of tuples, where each tuple contains (header, sequence).
    """
    sequences = []
    current_sequence = []
    header = None
    
    try:
        with open(fasta_file_path, 'r') as fasta_file:
            for line in fasta_file:
                line = line.strip()
                if line.startswith(">"):
                    # When encountering a new header, store the current sequence if it exists
                    if current_sequence and header:
                        sequences.append((header, ''.join(current_sequence)))
                        current_sequence = []
                    # Start a new sequence
                    header = line[1:]  # remove the '>' from the header
                else:
                    # Continue to append the sequence lines
                    current_sequence.append(line)

            # Append the last sequence if any
            if current_sequence and header:
                sequences.append((header, ''.join(current_sequence)))

    except FileNotFoundError:
        print(f"Error: The file '{fasta_file_path}' was not found.")
    except IOError as e:
        print(f"Error reading file: {e}")


    return sequences


def run_igblast(
        header,
        sequence,
        db = os.path.join(
          root_folder,
          'IgBlast',
          'igblast',
          'database',
          'Homo_sapiens_clean',
          'IG_prot',
          'IGLV_clean')):
    """
    Runs the 'igblast' command for a given sequence, captures the output, and returns it as a string.
    
    Parameters:
    sequence (str): The sequence to run igblast on.
    igblast_db (str): Path to the igblast database.

    Returns:
    str: The output from the igblast command.
    """
    
    try:

        #write input sequence to temporary file
        fileName = header.replace(" ","_")
        f = open(fileName + ".fasta", "a")
        f.write(">" + header+"\n")
        f.write(sequence)
        f.close()

        #print(f"Running igblast for {fileName}...")

        # This assumes igblast is in your PATH. Customize the command as needed for your environment.
        bin_igblastp = os.path.join('.','bin','igblastp')
        if isWindows:
            bin_igblastp = bin_igblastp + '.exe'

        cmd = [bin_igblastp, '-query', fileName + ".fasta", '-outfmt', '7', '-germline_db_V', db]
        print(cmd)
        # Run the subprocess, passing the sequence as input
        result = subprocess.run(cmd, text=True, capture_output=True, check=True)

        os.remove(fileName + ".fasta")

        # Return the output from igblast
        return result.stdout

    except subprocess.CalledProcessError as e:
        print(f"Error running igblast for the sequence: {e}")
        return None


def extract_igblast_output(output):
    """
    Extracts the table data from the igblast output and converts it into a pandas DataFrame.
    
    Parameters:
    output (str): The igblast output text.
    
    Returns:
    pd.DataFrame: The extracted table as a pandas DataFrame, or None if no table is found.
    """
    lines = output.splitlines()
    align_table_lines = []
    align_header = ["Region", "from", "to", "length", "matches", "mismatches", "gaps", "percent identity"]
    capturing_align_table = False
    
    match_table_lines = []
    match_header = ["DB"]
    capturing_match_table = False

    igblast_out = dict(alignment=None, matches=None)

    for line in lines:
        if line.startswith("# Alignment summary between query and top germline V gene hit"):
            capturing_align_table = True
        elif capturing_align_table:
            if line.strip() == "" or line.startswith("Total"):
                capturing_align_table = False
            else:
                align_table_lines.append(line)

        if line.startswith("# Fields: "):
            line = line.replace("# Fields: ", "")
            match_header  = match_header + line.split(", ") 
        elif line.startswith("hits found", 4):
            capturing_match_table = True
        elif capturing_match_table:
            if line.strip() == "" or line.startswith("# BLAST"):
                capturing_match_table =  False
            else:
                match_table_lines.append(line)            

    # Process the table into a DataFrame if table lines were found
    if align_table_lines:
        # Split lines into columns (assuming columns are separated by tabs or multiple spaces)
        align_data = [line.split("\t") for line in align_table_lines]

        # Identify header columns and the data rows
        align_rows = align_data[0:]  

        # Create the DataFrame
        align_df = pd.DataFrame(align_rows, columns=align_header)

        igblast_out['alignment'] = align_df
  
        
    if match_table_lines:
        # Split lines into columns (assuming columns are separated by tabs or multiple spaces)
        match_data = [line.split("\t") for line in match_table_lines]

        # the data rows
        match_rows = match_data[0:]  

        # Create the DataFrame
        match_df = pd.DataFrame(match_rows, columns=match_header)
        match_df.sort_values (by = '% identity', ascending=False) 

        igblast_out['matches'] = match_df.loc[0,'subject id':'% identity']

    return igblast_out


def process_sequences_with_igblast(sequences, dbs = [
    ("VH",
     os.path.join(
          root_folder,
          'IgBlast',
          'igblast',
          'database',
          'Homo_sapiens_clean',
          'IG_prot',
          'IGHV_clean')
    ),
    ("VL-lambda", os.path.join(
          root_folder,
          'IgBlast',
          'igblast',
          'database',
          'Homo_sapiens_clean',
          'IG_prot',
          'IGLV_clean')
    ),
    ("VL-kappa", os.path.join(
          root_folder,
          'IgBlast',
          'igblast',
          'database',
          'Homo_sapiens_clean',
          'IG_prot',
          'IGKV_clean')
    )]):
    """
    Process sequences by running igblast on each sequence and capturing the output.
    Extracts the table for each query and stores the data in pandas DataFrames.
    
    Parameters:
    sequences: dict with the sequence_id and the AA sequence
    
    Returns:
    dict: A dictionary where the keys are sequence headers and the values are pandas DataFrames.
    """
   
    results = dict()
    os.environ["IGDATA"] = os.path.join(
          root_folder,
          'IgBlast',
          'igblast')
    
    
    for header, sequence in sequences.items():
        print(f"Running igblast for {header}...")
        
        best_match = None

        for db_name, db in dbs:

            # Run igblast on the current sequence
            output = run_igblast(header, sequence, db)

            if output:
                # Extract the table from the igblast output
                igblast_out = extract_igblast_output(output)
                # add the sequence
                igblast_out.update({'sequence':sequence})
                igblast_out.update({'chain':db_name})

                if best_match is None or igblast_out['matches'].loc['% identity'] > best_match['matches'].loc['% identity']:
                    best_match = igblast_out

                if igblast_out is not None:
                    print(f"Extracted table for {header}:\n{igblast_out['matches']}")
                else:
                    print(f"No table found for {header}.")
            else:
                print(f"Failed to get output for {header}.")        
                    
        # Store the result in the dictionary 
        results[header] = best_match

    return results


def split_sequences_into_regions(data_dict):
    """
    Splits the sequence into substrings based on start and end points from the alignment table
    and returns a dictionary with 'Region' names as keys.

    Parameters:
    data_dict (dict): A dictionary with two keys:
                      'alignment' (pandas DataFrame): The table containing 'Region', 'from', and 'to' columns.
                      'sequence' (str): The full sequence to be split.
    
    Returns:
    dict: A dictionary where keys are the region names and values are the corresponding sequence substrings.
    """
    sequence = data_dict['sequence']
    alignment_table = data_dict['alignment']
    best_match = data_dict['matches']['subject id']
    chain = data_dict['chain']

    # Ensure that the DataFrame has at least 3 columns (Region, Start, and End)
    if not all(col in alignment_table.columns for col in ['Region', 'from', 'to']):
        raise ValueError("The alignment table must have 'Region', 'from', and 'to' columns.")

    # Extract region names, start points, and end points
    regions = alignment_table['Region']
    start_points = alignment_table['from'].astype(int) - 1  # Convert to zero-based indexing
    end_points = alignment_table['to'].astype(int)  # End points are inclusive, so no need to adjust

    # Create a dictionary to store substrings using regions as keys
    region_dict = {region: sequence[start:end] for region, start, end in zip(regions, start_points, end_points)}
    region_dict.update({'match':best_match})
    region_dict.update({'chain':chain})
    region_dict.update({'sequence' : sequence})

    return region_dict

def write_to_json(igblast_results, filename = "benchling_upload.json"):
    """
    Writes all results to a single JSON file.

    Parameters:
    igblast_output (list): A list of dictionaries where each dictionary has a 'sequence' and 'alignment' table.
    filename (str): The name of the output JSON file.
    """
    all_results = []

    # Loop through each element of igblast_output and process the sequence
    for header, out in igblast_results.items():
        result = split_sequences_into_regions(out)
        #print(f"Result for Sequence {header}:")
        #for region, substring in result.items():
        #    print(f"{region}: {substring}")
        #print()
        all_results.append({
            "sequence_id": header,  
            "results": result
        })
        
    # Write all results to a single JSON file
    try:
        with open(filename, 'w') as json_file:
            json.dump(all_results, json_file, indent=4)
        print(f"All results successfully written to {filename}")
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")

#def main():
    #"""
    #The main function to be executed when the script runs. It prompts the user for a file path and
    #extracts the 'Query=' blocks from the file.
    #"""
    
    #if len(sys.argv) < 2:
    #    print("ERROR. No argument provided to the file! Usage: python script.py <file_path>")
    #    return
    
    #file_path = sys.argv[1]
    #input_file_path ="/home/mvanmoerbeke/git/IgBlast/tests/seq-VH.fasta"
    
    #igblast_results = process_sequences_with_igblast(input_file_path)
    #write_to_json(igblast_results, filename = "benchling_upload.json")


#if __name__ == "__main__":
    #main()
