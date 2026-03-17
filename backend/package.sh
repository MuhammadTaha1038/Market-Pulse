pushd ./src/main
current_dir=$(pwd)
pip install --target ./temp_requirements -r ../../requirements.txt
cd ./temp_requirements
zip -r .requirements.zip .
cd $current_dir
cp ./temp_requirements/.requirements.zip .
rm -rf temp_requirements
zip -r py-lambda-pkg.zip .
mv py-lambda-pkg.zip ../../py-lambda-pkg.zip
