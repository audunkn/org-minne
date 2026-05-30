const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = {
  entry: "./src/taskpane.ts",
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "taskpane.bundle.js",
    clean: true,
  },
  resolve: {
    extensions: [".ts", ".js"],
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./src/taskpane.html",
      filename: "taskpane.html",
    }),
    new CopyWebpackPlugin({
      patterns: [{ from: "manifest.xml", to: "manifest.xml" }],
    }),
  ],
  devServer: {
    port: 3000,
    server: {
    type: 'https',
    options: {
      key: require('fs').readFileSync('./localhost-key.pem'),
      cert: require('fs').readFileSync('./localhost.pem'),
  },
},
    headers: {
      "Access-Control-Allow-Origin": "*",
    },
  },
};