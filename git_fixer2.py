import os
import time
import glob
import sys
import shutil
import argparse
import yaml

with open("config_git_fixer.yml") as stream:
    config = yaml.safe_load(stream)

GIT_FIXER_REMOVE = config['git_fixer_remove']
GIT_FIXER_IGNORE = config['git_fixer_ignore']


# Function to check if 'upstream' remote is set up
def check_upstream_remote():
    remotes = os.popen('git remote -v').read()
    if 'upstream' not in remotes:
        print("The 'upstream' remote is not set up. Please run the following command to set it up:")
        print("git remote add upstream <upstream-repository-url>")
        sys.exit(1)


# Check if the upstream remote is set up
check_upstream_remote()

# Fetch the latest updates from the upstream repository
os.system('git fetch upstream')

# Function to check if a file exists in the upstream repository
def file_exists_in_upstream(file_path):
    result = os.system(f'git ls-tree upstream/main -- {file_path} > /dev/null 2>&1')
    return result == 0  # Return True if the file exists, False if it doesn't

# Function to compare a local file with its upstream version
def compare_with_upstream(file_path):
    # First, check if the file exists in the upstream repository
    if not file_exists_in_upstream(file_path):
        print(f"File {file_path} does not exist in upstream. Skipping.")
        return None  # Return None to indicate no comparison needed
    
    # Create a temporary copy of the upstream version
    temp_file = "/tmp/{}".format(os.path.basename(file_path))
    os.system('git show upstream/main:{} > {}'.format(file_path, temp_file))

    # Compare the working copy with the upstream version
    result = os.system('cmp --silent "{}" "{}"'.format(file_path, temp_file))
    
    # Clean up the temporary file
    os.remove(temp_file)
    
    return result  # 0 if files are identical, non-zero if different

# Revert the original file to the upstream version
def revert_to_upstream(file_path):
    print("Reverting {} to upstream version.".format(file_path))
    os.system('git checkout upstream/main -- {}'.format(file_path))

# Iterate through all tracked files to find modifications
modified_files = []
os.system('git ls-tree -r main --name-only > tracked_files.txt')

to_remove = []
to_ignore = []
with open('tracked_files.txt', 'r') as f:
    for file_path in f.readlines():
        file_path = file_path.strip()

        # Ignore
        # - files that has already been copied with suffix MODIFIED 
        # - files in assignments directory
        ignore_patterns = ['MODIFIED', 'assignments/',]
        
        # Also take command line arguments for additional ignore patterns
        # Usage: python3 git_fixer2.py --ignore="some_file_name,some_directory_name/"
         
        if all(pattern not in glob.glob(pattern) for pattern in GIT_FIXER_IGNORE):
            # Compare each file with its upstream version
            result = compare_with_upstream(file_path)
            if result is not None and result != 0:
                modified_files.append(file_path)

# Create copies of modified files with a "_MODIFIED_" suffix
for file_path in modified_files:
    fname_extension = file_path.split('.')[-1]
    fname_prefix = '.'.join(file_path.split('.')[:-1])
    new_fname = "{}_MODIFIED_{}.{}".format(fname_prefix, int(time.time()), fname_extension)
    
    # Copy the original file to the new modified file
    shutil.copy(file_path, new_fname)
    print("Copied {} to {} for modification.".format(file_path, new_fname))
    
    # Revert the original file to the upstream version
    revert_to_upstream(file_path)

for wildcard in GIT_FIXER_REMOVE:
    os.system('rm -f {}'.format(wildcard))
# Now merge the upstream changes without affecting the original files
os.system('git merge --no-commit upstream/main')

# Clean up old modified files by keeping the most recent copy
for modified_file in modified_files:
    wildcard = "{}_MODIFIED_*".format(modified_file.split('.')[0])
    matching_files = sorted(glob.glob(wildcard))
    
    # If there are multiple modified copies, remove older duplicates
    for idx in range(1, len(matching_files)):
        if os.system('cmp --silent "{}" "{}"'.format(matching_files[0], matching_files[idx])) == 0:
            os.remove(matching_files[idx])
            print("Removed duplicate modified file: {}".format(matching_files[idx]))

os.system("git ls-files --others --exclude-standard > commit_us.txt")

with open("commit_us.txt", 'r') as f:
    print("don't forget to add/commit/push the following: \n")
    for line in f.readlines():
        print(line)
        if line.strip() not in GIT_FIXER_IGNORE:
            print(line)
        
