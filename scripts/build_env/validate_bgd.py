from envgenehelper.business_helper import get_bgd_object, get_namespaces
from envgenehelper import logger

def main():
    logger.info(f"Validating that all namespaces mentioned in BG domain object are available in namespaces")
    namespace_names = [ns.name for ns in get_namespaces()]
    bgd = get_bgd_object()
    for k,v in bgd:
        if not 'Namespace' in k:
            continue
        if v['name'] not in namespace_names:
            raise ValueError(f'Namespace mentioned in {k} is not available in namespaces directory')
    logger.info(f"Validation was successful")


if __name__ == "__main__":
    main()
