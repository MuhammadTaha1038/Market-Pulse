#!/bin/bash

if [[ $TF_VAR_lambda_layer == "" ]]; then
  echo "No Layer to install"; exit 0;
fi

export ENV="ci"
export LAYER_NAME_SUFFIX="$(cut -d':' -f 1 <<< $TF_VAR_lambda_layer)";
export LAYER_VERSION="$(cut -d':' -f 2 <<< $TF_VAR_lambda_layer)";
export LAYER_NAME="$APP_PREFIX-$ENV-$AWS_REGION_PRIMARY-$LAYER_NAME_SUFFIX";
echo $LAYER_NAME;
echo $LAYER_VERSION;

wget -O lambda-layer.zip $(aws lambda get-layer-version --layer-name "$LAYER_NAME" --version-number "$LAYER_VERSION" --region $AWS_REGION_PRIMARY --query 'Content.Location' --output text)

unzip lambda-layer.zip -d ./src/main/
#cd src/main
mv ./python/* ./
rm -rf python
