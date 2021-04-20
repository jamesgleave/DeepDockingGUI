'use strict';

const webpack = require('webpack'); // eslint-disable-line no-unused-vars

module.exports = {
  mode: 'development', //TODO: change to production when done
  entry: './src/index.js',
  output: {
    path: __dirname,
    filename: './public/js/bundle.js',
  },
  context: __dirname,
  devtool: 'source-map',
  resolve: {
      extensions: ['.js', '.jsx', '.css'],
      alias: {
          jquery: "../node_modules/jquery/src/jquery"
      },
      modules: ['node_modules']
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /(node_modules)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
      ,{
        test: /\.css$/i,
        use: ['style-loader', 'css-loader']
      },{
          // Now we apply rule for images
        test: /\.(png|jpe?g|gif|svg)$/,
        use: [
              {
                // Using file-loader for these files
                loader: "file-loader",

                // In options we can set different things like format
                // and directory to save
                options: {
                  outputPath: './public/webp-img'
                }
              }
            ]
      },{
        // Apply rule for fonts files
        test: /\.(woff|woff2|ttf|otf|eot)$/,
        use: [
              {
                // Using file-loader too
                loader: "file-loader",
                options: {
                  outputPath: './public/fonts'
                }
              }
            ]
      },{
        test: /\.(png|gif|cur|jpg)$/, 
        loader: 'url-loader', 
        query: { limit: 8192 }
      }
      ]
  }
};