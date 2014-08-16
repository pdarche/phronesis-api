$(document).ready(function(){
  var template

  $("#create input[type='submit']").on('click', function(ev){
    ev.preventDefault()
    var el        = $('#create')
      , stimulant = el.find('.stimulant').val()
      , amount    = el.find('.amount').val()
      , unit      = el.find('.unit').val()
      , timestamp = el.find('.datetime').val()
      , data;

    data = {
      'stimulant' : stimulant,
      'amount'    : amount,
      'unit'      : unit, 
      'timestamp' : timestamp
    }


    $.ajax({
      url: '/api/stimulants',
      type: 'POST',
      data: data,
      success: function(){
        alert('success')
      },
      error: function(){
        alert('error')
      }
    })
  })
})

function renderTemplates(template, papers){
  var source   = $(template).html()
    , tmpl     = Handlebars.compile(source)
    , html     = tmpl({"papers":papers});

  $('#papers').html(html)
}
