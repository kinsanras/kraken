import logging
import random
import statistics

import tool

log = logging.getLogger(__name__)


CITIES = ['Shanghai', 'Lagos', 'Istanbul', 'Karachi', 'Mumbai', 'Moscow', 'Sao Paulo', 'Beijing', 'Guangzhou', 'Delhi',
          'Lahore', 'Shenzhen', 'Seoul', 'Jakarta', 'Tianjin', 'Chennai', 'Tokyo', 'Cairo', 'Dhaka', 'Mexico', 'Kinshasa',
          'Bangalore', 'New York', 'London', 'Bangkok', 'Tehran', 'Dongguan', 'Ho Chi Minh City', 'Bogota', 'Lima',
          'Hong Kong', 'Hanoi', 'Hyderabad', 'Wuhan', 'Rio de Janeiro', 'Foshan', 'Ahmedabad', 'Baghdad', 'Singapore',
          'Shantou', 'Riyadh', 'Jeddah', 'Santiago', 'Saint Petersburg', 'Qalyubia', 'Chengdu', 'Alexandria', 'Ankara',
          'Chongqing', 'Kolkata', 'Xian', 'Surat', 'Johannesburg', 'Nanjing', 'Dar es Salaam', 'Yangon', 'Abidjan',
          'Harbin', 'Zhengzhou', 'Suzhou', 'Sydney', 'New Taipei City', 'Los Angeles', 'Melbourne', 'Cape Town',
          'Shenyang', 'Yokohama', 'Busan', 'Hangzhou', 'Quanzhou', 'Durban', 'Casablanca', 'Algiers', 'Berlin', 'Nairobi',
          'Hefei', 'Kabul', 'Pyongyang', 'Madrid', 'Ekurhuleni', 'Pune', 'Addis Ababa', 'Changsha', 'Jaipur', 'Xuzhou',
          'Wenzhou']

ANIMALS = ['Aardvark', 'Albatross', 'Alligator', 'Alpaca', 'Ant', 'Anteater', 'Antelope', 'Ape', 'Armadillo', 'Donkey',
           'Baboon', 'Badger', 'Barracuda', 'Bat', 'Bear', 'Beaver', 'Bee', 'Bison', 'Boar', 'Buffalo', 'Galago',
           'Butterfly', 'Camel', 'Caribou', 'Cat', 'Caterpillar', 'Cattle', 'Chamois', 'Cheetah', 'Chicken', 'Chimpanzee',
           'Chinchilla', 'Chough', 'Clam', 'Cobra', 'Cockroach', 'Cod', 'Cormorant', 'Coyote', 'Crab', 'Crane', 'Crocodile',
           'Crow', 'Curlew', 'Deer', 'Dinosaur', 'Dog', 'Dogfish', 'Dolphin', 'Dotterel', 'Dove', 'Dragonfly', 'Duck',
           'Dugong', 'Dunlin', 'Eagle', 'Echidna', 'Eel', 'Eland', 'Elephant', 'Elk', 'Emu', 'Falcon', 'Ferret', 'Finch',
           'Fish', 'Flamingo', 'Fly', 'Fox', 'Frog', 'Gaur', 'Gazelle', 'Gerbil', 'Giant Panda', 'Giraffe', 'Gnat', 'Gnu',
           'Goat', 'Goose', 'Goldfinch', 'Goldfish', 'Gorilla', 'Goshawk', 'Grasshopper', 'Grouse', 'Guanaco', 'Gull',
           'Hamster', 'Hare', 'Hawk', 'Hedgehog', 'Heron', 'Herring', 'Hippopotamus', 'Hornet', 'Horse', 'Human',
           'Hummingbird', 'Hyena', 'Jackal', 'Jaguar', 'Jay', 'Jellyfish', 'Kangaroo', 'Koala', 'Kouprey', 'Kudu',
           'Lapwing', 'Lark', 'Lemur', 'Leopard', 'Lion', 'Llama', 'Lobster', 'Locust', 'Loris', 'Louse', 'Lyrebird',
           'Magpie', 'Mallard', 'Manatee', 'Marten', 'Meerkat', 'Mink', 'Mole', 'Monkey', 'Moose', 'Mouse', 'Mosquito',
           'Mule', 'Narwhal', 'Newt', 'Nightingale', 'Octopus', 'Okapi', 'Opossum', 'Oryx', 'Ostrich', 'Otter', 'Owl',
           'Ox', 'Oyster', 'Panther', 'Parrot', 'Partridge', 'Peafowl', 'Pelican', 'Penguin', 'Pheasant', 'Pig', 'Pigeon',
           'Porcupine', 'Porpoise', 'Quail', 'Quelea', 'Rabbit', 'Raccoon', 'Rail', 'Ram', 'Rat', 'Raven', 'Reindeer',
           'Rhinoceros', 'Rook', 'Ruff', 'Salamander', 'Salmon', 'Sandpiper', 'Sardine', 'Scorpion', 'Seahorse', 'Seal',
           'Shark', 'Sheep', 'Shrew', 'Shrimp', 'Skunk', 'Snail', 'Snake', 'Spider', 'Squid', 'Squirrel', 'Starling',
           'Stingray', 'Stinkbug', 'Stork', 'Swallow', 'Swan', 'Tapir', 'Tarsier', 'Termite', 'Tiger', 'Toad', 'Trout',
           'Turkey', 'Turtle', 'Vicuna', 'Viper', 'Vulture', 'Wallaby', 'Walrus', 'Wasp', 'Weasel', 'Whale', 'Wolf',
           'Wolverine', 'Wombat', 'Woodcock', 'Woodpecker', 'Worm', 'Wren', 'Yak', 'Zebra']


def _generate_test_case_name():
    animal = random.choice(ANIMALS).replace(' ', '-')
    city = random.choice(CITIES).replace(' ', '-')
    return "test_%s_%s.from.%s" % (animal, random.randint(0, 100000), city)


def collect_tests(step):
    random.seed(1)
    count = int(step.get('count', 10))
    tests = []
    for _ in range(count):
        tests.append(_generate_test_case_name())
    return tests


def run_tests(step, report_result=None):
    tests = step['tests']

    for test in tests:
        cmd = 'random_test %s' % test

        result = dict(cmd=cmd, test=test, status=random.choice([0, 1, 2, 3, 4, 5]))

        num = random.randint(0, 3)
        if num > 0:
            result['values'] = {}
            for name in random.sample(['FPS', 'pressure', 'speed', 'duration', 'temperature'], num):
                population = random.choices(range(random.choice([100, 1000, 10000])), k=random.choice([10, 50, 100]))
                pmin = min(population)
                pmax = max(population)
                pstdev = statistics.stdev(population)
                pmean = statistics.mean(population)
                val = {'value': pmean,
                       'median': statistics.median_low(population),
                       'min': pmin,
                       'max': pmax,
                       'range': pmax - pmin,
                       'stddev': pstdev,
                       'variance': statistics.variance(population),
                       'cv': pstdev / pmean,
                       'iterations': len(population)}
                try:
                    val['mode'] = statistics.mode(population)
                except:
                    pass
                result['values'][name] = val

        report_result(result)

    return 0, ''


if __name__ == '__main__':
    tool.main()
