' runs test1.html against FF
'saves results as results_fx_staging_TrustAfrica_suite.html

echo " runs test1.html against FF"
echo "saves results as results_fx_staging_TrustAfrica_suite.html"

java -jar "selenium-server-1.0.1\selenium-server.jar" -htmlSuite "*firefox" "http://staging.trustafrica.sixfeetup.com/" "../staging_suite.html" "../log/results_fx_staging_trustafrica_Suite.html"

