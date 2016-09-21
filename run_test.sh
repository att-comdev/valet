
sudo tox -epy27 -- -nvalet.tests.functional.valet_validator.tests.$*

# EXAMPLE:
# run specific tests:
# ./run_test test_affinity


# sudo tox -epy27 -- -nvalet.tests.functional.valet_validator.tests.test_affinity
# sudo tox -epy27 -- -nvalet.tests.functional.valet_validator.tests.test_exclusivity
# sudo tox -epy27 -- -nvalet.tests.functional.valet_validator.tests.test_affinity
# sudo tox -epy27 -- -nvalet.tests.functional.valet_validator.tests.test_diversity
