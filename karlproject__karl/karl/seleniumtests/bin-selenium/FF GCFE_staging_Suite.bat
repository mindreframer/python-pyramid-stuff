' runs test1.html against FF
'saves results as results_fx_GCFE_staging_Suite.html

echo " runs test1.html against FF"
echo "saves results as results_fx_GCFE_staging_Suite.html"

java -jar "selenium-server-1.0.1\selenium-server.jar" -htmlSuite "*firefox" "http://staging.gcfe.sixfeetup.com/" "../staging_suite1.html" "../log/results_fx_GCFE_staging_Suite.html"

