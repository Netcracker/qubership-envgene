from envgenehelper.business_helper import get_bgd_object, get_namespaces
from envgenehelper import logger

def main():
    logger.info(f'Validating that all namespaces mentioned in BG domain object are available in namespaces')
    namespace_names = [ns.name for ns in get_namespaces()]
    bgd = get_bgd_object()
    mismatch = ""
    for k,v in bgd.items():
        if not 'Namespace' in k:
            continue
        if v['name'] not in namespace_names:
            mismatch += (f"\n{v['name']} from {k}")
    if mismatch:
        logger.info(f'Available namespaces: {namespace_names}')
        raise ValueError(f'Next namespaces were not found in available namespaces: {mismatch}')
    logger.info(f'Validation was successful')


if __name__ == "__main__":
    main()
