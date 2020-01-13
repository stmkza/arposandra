module.exports = {
    mode: "development",
    entry: {
        "early": "./js/entry.js",
        "main": "./js/late_entry.js",
    },
    output: {
        filename: "[name].bundle.js",
        sourceMapFilename: "[name].bundle.js.map",
        publicPath: "http://localhost:5002/static/js/",
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: [/node_modules/, /lang/],
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: ["@babel/react"],
                        plugins: ["@babel/plugin-syntax-dynamic-import"]
                    }
                }
            },
        ]
    },
    devServer: {
        compress: true,
        port: 5002,
        headers: {"Access-Control-Allow-Origin": "*"},
    },
    optimization: {
        splitChunks: { chunks: "all" }
    }
}
