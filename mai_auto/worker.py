"""One upstream invocation per process, avoiding imports named utils/prompts colliding."""
import json
from pathlib import Path
import sys
from .native import call


def main():
    job = json.loads(Path(sys.argv[1]).read_text())
    result = call(job['adapter'], Path(job['source']), job['input'],
                  Path(job['output']), job.get('model'))
    # Strict JSON serialization: never silently stringify an upstream result object.
    Path(job['output'], 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
