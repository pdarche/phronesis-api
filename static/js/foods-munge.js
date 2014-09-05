$(document).ready(function(){
  var template
  $.get('/static/js/templates/foods-munge.handlebars', function(data){
    template = data
  })    
    
  $.getJSON('/api/foods', function(data){
    console.log('the data', data)
    renderTemplates(template, data)
  })
})

function renderTemplates(template, foods){
  var source   = $(template).html()
    , tmpl     = Handlebars.compile(source)
    , html     = tmpl({"foods":foods});

  $('#food_photos_container').html(html)
}