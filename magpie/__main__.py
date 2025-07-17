import pathlib
import runpy
import sys

root = pathlib.Path(__file__).parent.parent
all_valid_targets = [path for paths in [sorted(root.glob(f'magpie/{d}/*.py')) for d in ['bin', 'scripts']] for path in paths if '__init__' not in path.name]
valid_protocols = {
    '/magpie/bin/software_improvement' :
        ['local_search', 'genetic_programming'],
    '/magpie/bin/patch_operations' :
        ['ablation_analysis', 'minify_patch', 'revalidate_patch'],
    '/magpie/bin/visualizer' :
        ['show_location', 'show_patch']
}

def usage():
    print('usage: python3 magpie ((magpie/){bin,scripts}/)TARGET(.py) [ARGS]...')
    print('possible TARGET:', file=sys.stderr)
    cwd = pathlib.Path.cwd()
    for path in all_valid_targets:
        print(f'    {path.stem:16}	({path.relative_to(cwd)})', file=sys.stderr)

def get_valid_target(argv):
    if len(argv) < 2:
        return None
    path = pathlib.PurePath(argv[1])
    for target in all_valid_targets:
        if path.stem == target.stem:
            return f'magpie.{target.parent.name}.{path.stem}'
    return None

def get_valid_protocol(argv):
    given_protocol = argv[1]
    for valid_protocol in valid_protocols.keys():
        if valid_protocols[valid_protocol].__contains__(given_protocol):
            path = pathlib.PurePath(valid_protocol)
            return f'magpie.{path.parent.name}.{path.stem}'
    return None

if __name__ == '__main__':
    valid_target = get_valid_target(sys.argv)
    if not valid_target:
        prot = get_valid_protocol(sys.argv)
        if not prot:
            usage()
            sys.exit(1)
        print(prot)
        sys.path.append(str(root.resolve()))
        runpy.run_module(prot, run_name='__main__', alter_sys=True)
    elif valid_target.__contains__('magpie.scripts') :
        sys.argv = sys.argv[1:]
        sys.path.append(str(root.resolve()))
        runpy.run_module(valid_target, run_name='__main__', alter_sys=True)


