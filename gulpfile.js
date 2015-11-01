var gulp = require('gulp');
var browserify = require('browserify');
var babelify = require('babelify');
var source = require('vinyl-source-stream');
var watch = require('gulp-watch');
var livereload = require('gulp-livereload');

gulp.task('build', function() {
    browserify({
        entries: 'src/index.js',
        extensions: ['.js'],
        debug: true,
    })
    .transform(babelify)
    .bundle()
    .pipe(source('bundle.js'))
    .pipe(gulp.dest('static/js'))
    .pipe(livereload());
});

gulp.task('default', ['build']);

gulp.task('watch', function() {
    livereload.listen();
    gulp.watch('src/*.js', ['build']);
});
