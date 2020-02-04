import sys
import yaml
import subprocess

if len(sys.argv) < 2 :
    print("Explicit at least an HEP-score input yaml")
    exit(1) 

print('Argument List: %s' % str(sys.argv))

for inputfile in sys.argv[1:]:
    print("\nProcessing file %s" % inputfile)
    config = yaml.safe_load(open(inputfile).read())
    
    try:
        for bmk in sorted(config['hepscore_benchmark']['benchmarks'].keys()):
            if bmk[0] == ".":
                continue
            image_path = config['hepscore_benchmark']['registry']+'/'+bmk+':'+config['hepscore_benchmark']['benchmarks'][bmk]['version']
            print("\tImage path %s" % image_path)
            bashCommand="skopeo inspect docker://" + image_path
            subprocess.check_output(bashCommand.split())
    except:
        exit(1)
exit(0)