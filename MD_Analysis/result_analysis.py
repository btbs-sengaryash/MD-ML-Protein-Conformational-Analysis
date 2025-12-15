import argparse
import logging
import os
import shutil
import fnmatch
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)  # Set the logging level to INFO

# Set up argument parsing
parser = argparse.ArgumentParser(description='Automate result analysis of protein-ligand MD simulation from Gromacs.')
parser.add_argument('--mode', choices=['gmx_mmpbsa', 'gmx_mmpbsa_post_clean', 'plip_xml_summary'], default="gmx_mmpbsa", required=True, help='Select the type of Analysis. Eg: gmx_mmpbsa')
parser.add_argument('--start', type=float, required=False, help='Start time frame (ns) for GMX_MMPBSA Calculation')
parser.add_argument('--end', type=float, required=False, help='End time frame (ns) for GMX_MMPBSA Calculation')
parser.add_argument('--time_step', type=float, default=0.01, help='Time step used in MD simulation (in ns). Default: 0.01')
parser.add_argument('--decompose', action='store_true', help='Flag to enable decomposition analysis')
parser.add_argument('--decomp_type', choices=['residue', 'energy_term'], default='residue', 
                    help='Decomposition type: residue-wise (default) or energy term-based')
parser.add_argument('--interval_ns', type=float, default=10, help='Interval for snapshots in ns. Default: 10')

args = parser.parse_args()

# Path to the input file
input_file = "mmpbsa_base.in"
output_file = "mmpbsa.in"

# If current mode is to analyze for GMX_MMPBSA
if args.mode == 'gmx_mmpbsa':
# Calculate the corresponding frame numbers
  start_frame = int(args.start / args.time_step)
  end_frame = int(args.end / args.time_step)
  # Log the calculated frame numbers
  logging.info(f"Start frame: {start_frame}")
  logging.info(f"End frame: {end_frame}")
  try:
      # Read and modify the input file
      with open(input_file, 'r') as file:
          lines = file.readlines()

      # Modify the startframe and endframe values
      with open(output_file, 'w') as file:
          for line in lines:
              if line.strip().startswith("startframe"):
                  file.write(f"startframe={start_frame},\n")
              elif line.strip().startswith("endframe"):
                  file.write(f"endframe={end_frame},\n")
              else:
                  file.write(line)

      logging.info(f"Modified input file written to {output_file}")

  except FileNotFoundError:
      logging.error(f"Input file '{input_file}' not found.")
  except Exception as e:
      logging.error(f"An error occurred: {e}")

# If current mode is to analyze for GMX_MMPBSA
if args.mode == 'gmx_mmpbsa_post_clean':
  try:
    # Define the source directory (current directory) and target folder
    source_dir = os.getcwd()
    target_folder = os.path.join(source_dir, "gmx_mmpbsa")

    # Create the target folder if it doesn't exist
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f"Created folder: {target_folder}")

    # Move files matching the pattern '_GMXMMPBSA*' to the target folder
    file_pattern = "_GMXMMPBSA*"
    moved_files = []

    for filename in os.listdir(source_dir):
        if fnmatch.fnmatch(filename, file_pattern):
            source_file = os.path.join(source_dir, filename)
            target_file = os.path.join(target_folder, filename)
            shutil.move(source_file, target_file)
            moved_files.append(filename)
  except FileNotFoundError:
      logging.error(f"Files matching the pattern not found.")

# Add conditional block for PLIP XML summary and plotting
if args.mode == 'plip_xml_summary':
    def extract_interaction_counts(xml_file):
        bond_types = [
            "hydrogen_bonds", "hydrophobic_interactions", "halogen_bonds", "metal_complexes",
            "pi_cation_interactions", "pi_stacks", "salt_bridges", "water_bridges"
        ]
        counts = {k: 0 for k in bond_types}
        if not xml_file or not xml_file.endswith(".xml") or not os.path.exists(xml_file):
            return counts
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for site in root.findall(".//bindingsite"):
                interactions = site.find("interactions")
                if interactions is not None:
                    for child in interactions:
                        tag = child.tag
                        if tag in counts:
                            counts[tag] += len(child.findall("*"))
        except Exception:
            pass
        return counts
    # Use snap_*.pdb and .xml files
    snapshots_dir = 'snapshots'
    interval_ns = args.interval_ns if hasattr(args, 'interval_ns') and args.interval_ns else 10
    output_csv = os.path.join(snapshots_dir, 'plip_summary.csv')
    bond_types = [
        "hydrogen_bonds", "hydrophobic_interactions", "halogen_bonds", "metal_complexes",
        "pi_cation_interactions", "pi_stacks", "salt_bridges", "water_bridges"
    ]
    rows = []
    for pdb in sorted(os.listdir(snapshots_dir)):
        if pdb.startswith('snap_') and pdb.endswith('.pdb'):
            serial = int(pdb[len('snap_'):-4])
            timescale = serial * interval_ns
            xml_file = os.path.join(snapshots_dir, f"snap_{serial}.xml")
            counts = extract_interaction_counts(xml_file)
            row = [timescale] + [counts[b] for b in bond_types]
            rows.append(row)
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timescale_ns"] + bond_types)
        writer.writerows(rows)
    print(f"Summary written to {output_csv}")


