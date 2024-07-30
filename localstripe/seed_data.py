from glob import glob
import json
import os.path
import logging

from aiohttp.web_runner import GracefulExit

from .errors import UserError
from .resources import Product, Plan, Price, Coupon


async def seed_if_does_not_exist(cls, data, logger):
    if not isinstance(data, list):
        raise UserError(400,
                        ('incorrect format'
                         '(data provided for %s must be a list)' % cls.object))

    for datum in data:
        try:
            cls._api_create(**datum)._export()
            logger.info((f'Successfully created {cls.object}'
                        f": {datum.get('id')}"))
        except UserError as e:
            if (e.code == 409):
                logger.info(('Ignoring already seeded {cls.object}: '
                            f"{datum.get('id')}"))
                pass
            else:
                logger.error((f'Error seeding {cls.object} '
                              f"({datum.get('id')}): "
                              f'{e.body}'))
        except Exception as e:
            logger.error(f'Incorrect format for {cls.object}: {e}. Skipping.')


async def seed_data(app):
    logger = logging.getLogger('aiohttp.access')

    try:
        seed_dir = app['seed_dir']
        seed_path_glob = os.path.join(seed_dir, "*.json")

        file_list = glob(seed_path_glob)
        if not file_list:
            logger.warn(('\n\n!!! WARNING: '
                         f'No fixture file found in directory: {seed_dir}/'
                         '!!!'))
            return logger.warn("Data store will not be seeded.\n")

        for path in file_list:
            if os.path.isfile(path):
                logger.info("\nSeeding data from file: %s...\n", path)
                file = open(path)
                data = json.load(file)

                for key in data:
                    match key:
                        case 'products':
                            await seed_if_does_not_exist(Product, data[key],
                                                         logger)
                        case 'plans':
                            await seed_if_does_not_exist(Plan, data[key],
                                                         logger)
                        case 'prices':
                            await seed_if_does_not_exist(Price, data[key],
                                                         logger)
                        case 'coupons':
                            await seed_if_does_not_exist(Coupon, data[key],
                                                         logger)
                        case _:
                            logger.error("Unimplemented Error: %s", key)
        logger.info("\n...Success!\n")
    except json.JSONDecodeError as e:
        logger.error("Seed Failed!!! Error decoding JSON seed file: %s\n", e)
        raise GracefulExit()
    except Exception as e:
        logger.error(('Seed Failed!!!'
                      f'Error seeding data store with data file: {e}\n'))
        raise GracefulExit()
