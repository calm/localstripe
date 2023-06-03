from .errors import UserError
from .resources import Product, Plan, Price, Coupon

from glob import glob
import json
import os.path
import logging

async def seed_if_does_not_exist(cls, data, logger):
    for datum in data:
        try:
            cls._api_create(**datum)._export()
            logger.info("Successfully created %s: %s" %(cls.object, datum.get('id')))
        except UserError as e:
            if (e.code == 409):
                logger.info("Ignoring already seeded %s: %s" %(cls.object, datum.get('id')))
                pass
            else:
                logger.error("Error seeding %s (%s): %s" %(cls.object, datum.get('id'), e.body))

async def seed_data(app):
    try:
        logger = logging.getLogger('aiohttp.access')

        seed_dir = app['seed_dir']
        seed_path_glob = os.path.join(seed_dir, "*.json")

        for path in glob(seed_path_glob):
            if os.path.isfile(path):
                logger.info("\nSeeding data from file: %s...\n", path)
                file = open(path)
                data = json.load(file)

                for key in data:
                    match key:
                        case 'products':
                            await seed_if_does_not_exist(Product, data[key], logger)
                        case 'plans':
                            await seed_if_does_not_exist(Plan, data[key], logger)
                        case 'prices':
                            await seed_if_does_not_exist(Price, data[key], logger)
                        case 'coupons':
                            await seed_if_does_not_exist(Coupon, data[key], logger)
                        case _:
                            logger.error("Unimplemented Error: %s", key)
    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON seed file: %s", e)
    finally:
        logger.info("\n...Done!\n")
