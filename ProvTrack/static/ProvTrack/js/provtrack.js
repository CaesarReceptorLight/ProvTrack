/*
 * Dependencies:
 * - d3.js
 * - jquery.js
 */

 /*
 * Code adapted from d3js-tree-boxes (MIT License)
 */

/*
 * Email: caesar@uni-jena.de
 */

"use strict";

function ProvTrackGraph(urlService, jsonData, view)
{

	var urlService_ = '';

	var blue = '#337ab7',
		green = '#5cb85c',
		yellow = '#f0ad4e',
		blueText = '#4ab1eb',
		brown = '#8D6E63',
		cyan = '#80deea',
		white = '#FFFFFF',
		red = '#E53935',
		purple = '#9467bd';


	var margin = {
					top : 0,
					right : 0,
					bottom : 100,
					left : 0
				 },
		// Height and width are redefined later in function of the size of the tree
		// (after that the data are loaded)
		width = 800 - margin.right - margin.left,
		height = 400 - margin.top - margin.bottom;

	var rectNode = { width : 120, height : 45, textMargin : 5 },
		tooltip = { width : 150, height : 40, textMargin : 5 };
	var i = 0,
		duration = 750,
		select2_data,
		paths,
		root;

	var mousedown; // Use to save temporarily 'mousedown.zoom' value
	var mouseWheel,
		mouseWheelName,
		isKeydownZoom = false;

	var tree;
	var baseSvg,
		svgGroup,
		nodeGroup, // If nodes are not grouped together, after a click the svg node will be set after his corresponding tooltip and will hide it
		nodeGroupTooltip,
		linkGroup,
		linkGroupToolTip,
		defs;

	init(urlService, jsonData, view);

	function init(urlService, jsonData, view)
	{
		urlService_ = urlService;
		if (urlService && urlService.length > 0)
		{
			if (urlService.charAt(urlService.length - 1) != '/')
				urlService_ += '/';
		}

		if (jsonData) {

			drawProvTrackGraph(jsonData);
		}
		else
		{
			console.error(jsonData);
			alert('Invalides data.');
		}
	}

	function drawProvTrackGraph(jsonData)
	{
		tree = d3.layout.tree().size([ height, width ]);
		root = jsonData;
		root.fixed = true;

		select2_data = extract_select2_data(jsonData,[],0)[1];

		// Dynamically set the height of the main svg container
		// breadthFirstTraversal returns the max number of node on a same level
		// and colors the nodes
		var maxDepth = 0;
		var maxTreeWidth = breadthFirstTraversal(tree.nodes(root), function(currentLevel) {
			maxDepth++;
			currentLevel.forEach(function(node) {
				if (node.ontologyClassType == 'entity' || node.ontologyClassType == 'http://www.w3.org/ns/prov#Entity' || node.ontologyClassType == 'http://purl.org/net/p-plan#Entity')
					node.color = blue;
				if (node.ontologyClassType == 'plan' || node.ontologyClassType == 'http://purl.org/net/p-plan#Plan' || node.ontologyClassType == 'http://www.w3.org/ns/prov#Plan')
					node.color = green;
				if (node.ontologyClassType == 'step' || node.ontologyClassType == 'http://purl.org/net/p-plan#Step')
					node.color = yellow;
				if (node.ontologyClassType == 'variable' || node.ontologyClassType == 'http://purl.org/net/p-plan#Variable')
					node.color = brown;
				if (node.ontologyClassType == 'agent' || node.ontologyClassType == 'http://www.w3.org/ns/prov#Agent')
					node.color = cyan;
				if (node.ontologyClassType == 'activity' || node.ontologyClassType == 'http://www.w3.org/ns/prov#Activity')
					node.color = purple;
				});
			});
		// height = maxTreeWidth * (rectNode.height + 20) + tooltip.height + 20 - margin.right - margin.left;
		// width = maxDepth * (rectNode.width * 1.5) + tooltip.width / 2 - margin.top - margin.bottom;

		$('#tree-container').append('<div>' +
			'<div class="dropdown">' +
			'<button class="dropbtn"><i class="fas fa-palette dropbtn" ></i></button>' +
			'<div class="dropdown-content">' +
				'<div style="color:#337ab7;">Entity</div>' +
				'<div style="color:#80deea;">Agent</div>' +
				'<div style="color:#9467bd;">Activity</div>' +
				'<div style="color:#5cb85c;">Plan</div>' +
				'<div style="color:#8D6E63;">Variable</div>' +
				'<div style="color:#f0ad4e;">Step</div>' +
			'</div>' +
			'</div>' +
		'</div>');

		$('#tree-container').append('<div id="expand">' +
		'<button class="toolbar_button" title="Expand All"><i class="fas fa-expand"></i></button>' +
		'</div>');

		$('#tree-container').append('<div id="collapse">' +
		'<button class="toolbar_button" title="Collapse All"><i class="fas fa-compress"></i></button>' +
		'</div>');

		// tree = d3.layout.tree().size([ height, width ]);
		root.x0 = height / 2;
		root.y0 = 0;

		// Code snippet to flatten the root on initialisation
		// root.x0 = 0;
		// root.y0 = 0;
		collapse(jsonData);
		// root.children.forEach(collapse);


		baseSvg = d3.select('#tree-container').append('svg')
	    .attr('width', width + margin.right + margin.left)
		.attr('height', height + margin.top + margin.bottom)
		.attr('class', 'svgContainer')
		.call(d3.behavior.zoom()
		      //.scaleExtent([0.5, 1.5]) // Limit the zoom scale
		      .on('zoom', zoomAndDrag));

		// Mouse wheel is desactivated, else after a first drag of the tree, wheel event drags the tree (instead of scrolling the window)
		getMouseWheelEvent();
		d3.select('#tree-container').select('svg').on(mouseWheelName, null);
		d3.select('#tree-container').select('svg').on('dblclick.zoom', null);

		svgGroup = baseSvg.append('g')
		.attr('class','drawarea')
		.append('g')
		.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

		// SVG elements under nodeGroupTooltip could be associated with nodeGroup,
		// same for linkGroupToolTip and linkGroup,
		// but this separation allows to manage the order on which elements are drew
		// and so tooltips are always on top.
		nodeGroup = svgGroup.append('g')
					.attr('id', 'nodes');
		linkGroup = svgGroup.append('g')
					.attr('id', 'links');
		linkGroupToolTip = svgGroup.append('g')
			   				.attr('id', 'linksTooltips');
		nodeGroupTooltip = svgGroup.append('g')
			   				.attr('id', 'nodesTooltips');

		defs = baseSvg.append('defs');
		initArrowDef();
		initDropShadow();

		$("#searchPath").select2({
			data: select2_data,
			containerCssClass: "search"
		});

		$("#searchPath").on("select2-selecting", function(e) {
			if(typeof(paths) !== "undefined") {
				clearPaths(paths);
			}
			paths = searchTree(root,e.object.text,[]);
			if(typeof(paths) !== "undefined"){
				openPaths(paths);
				updateInfoBox(paths[paths.length-1]); //Update the Infobox for the clicked node
			}
			// else{
			// 	alert(e.object.text+" not found!");
			// }
		});

		$('#expand').on('click', function() {
			expandAll(root);
			update(root);
		});

		$('#collapse').on('click', function() {
			collapse(root);
			update(root);
		});


		update(root);
	}

	function collapse(node) {
		if(node.children) {
			node.children.forEach(function(c) { collapse(c); });
			node._children = node.children;
			node.children = null;
		}
	}

	function expandAll(d) {
		var children = (d.children)?d.children:d._children;
		if (d._children) {
			d.children = d._children;
			d._children = null;
		}
		if(children)
			children.forEach(function(c) { expandAll(c); });

		// update(root);
	}

	function update(source)
	{

		var maxDepth = 0;
		var maxTreeWidth = breadthFirstTraversal(tree.nodes(root), function(currentLevel) {
			maxDepth++;
		});
		height = maxTreeWidth * (rectNode.height + 20) + tooltip.height + 20 - margin.right - margin.left;
		width = maxDepth * (rectNode.width * 1.5) + tooltip.width / 2 - margin.top - margin.bottom;


		tree = d3.layout.tree().size([ height, width ]);

		d3.select('#tree-container').select('svg')
			.attr("width", width + margin.right + margin.left + 200)
			.attr("height", height + margin.top + margin.bottom + 200);

		// Compute the new tree layout
		var nodes = tree.nodes(root).reverse(),
			links = tree.links(nodes);

		// Check if two nodes are in collision on the ordinates axe and move them
		breadthFirstTraversal(tree.nodes(root), collision);
		// Normalize for fixed-depth
		nodes.forEach(function(d) {
			d.y = d.depth * (rectNode.width * 1.5);
		});

	// 1) ******************* Update the nodes *******************
		var node = nodeGroup.selectAll('g.node').data(nodes, function(d) {
			return d.id || (d.id = ++i);
		});
		var nodesTooltip = nodeGroupTooltip.selectAll('g').data(nodes, function(d) {
			return d.id || (d.id = ++i);
		});

		// Enter any new nodes at the parent's previous position
		// We use "insert" rather than "append", so when a new child node is added (after a click)
		// it is added at the top of the group, so it is drawed first
		// else the nodes tooltips are drawed before their children nodes and they
		// hide them
		var nodeEnter = node.enter().insert('g', 'g.node')
		.attr('class', 'node')
		.attr('transform', function(d) {
			  return 'translate(' + source.y0 + ',' + source.x0 + ')'; })
		.on('click', function(d) {
				click(d);
		});
		var nodeEnterTooltip = nodesTooltip.enter().append('g')
			.attr('transform', function(d) {
				  return 'translate(' + source.y0 + ',' + source.x0 + ')'; });

		nodeEnter.append('g').append('rect')
		.attr('rx', 6)
		.attr('ry', 6)
		.attr('width', rectNode.width)
		.attr('height', rectNode.height)
		.attr('class', 'node-rect')
		.attr('fill', function (d) { return d.color; })
		.attr('filter', 'url(#drop-shadow)');

		nodeEnter.append('foreignObject')
		.attr('x', rectNode.textMargin)
		.attr('y', rectNode.textMargin)
		.attr('width', function() {
					return (rectNode.width - rectNode.textMargin * 2) < 0 ? 0
							: (rectNode.width - rectNode.textMargin * 2)
				})
		.attr('height', function() {
					return (rectNode.height - rectNode.textMargin * 2) < 0 ? 0
							: (rectNode.height - rectNode.textMargin * 2)
				})
		.append('xhtml').html(function(d) {
					return '<div style="width: '
							+ (rectNode.width - rectNode.textMargin * 2) + 'px; height: '
							+ (rectNode.height - rectNode.textMargin * 2) + 'px;" class="node-text wordwrap">'
							+ '<b>' + d.name + '</b><br><br>'
							// + '<b>Class: </b>' + d.ontologyClass + '<br>'
							// + '<b>Version: </b>' + d.version + '<br>'
							+ '</div>';
				})
		.on('mouseover', function(d) {
			$('#nodeInfoID' + d.id).css('visibility', 'visible');
			$('#nodeInfoTextID' + d.id).css('visibility', 'visible');
		})
		.on('mouseout', function(d) {
			$('#nodeInfoID' + d.id).css('visibility', 'hidden');
			$('#nodeInfoTextID' + d.id).css('visibility', 'hidden');
		});

		nodeEnterTooltip.append("rect")
		.attr('id', function(d) { return 'nodeInfoID' + d.id; })
    	.attr('x', rectNode.width / 2)
		.attr('y', rectNode.height / 2)
		.attr('width', tooltip.width + 50)
		.attr('height', tooltip.height)
    	.attr('class', 'tooltip-box')
		.style('fill-opacity', 0.8)
		.style('fill', 'white')
		.on('mouseover', function(d) {
			$('#nodeInfoID' + d.id).css('visibility', 'visible');
			$('#nodeInfoTextID' + d.id).css('visibility', 'visible');
			removeMouseEvents();
		})
		.on('mouseout', function(d) {
			$('#nodeInfoID' + d.id).css('visibility', 'hidden');
			$('#nodeInfoTextID' + d.id).css('visibility', 'hidden');
			reactivateMouseEvents();
		});

		nodeEnterTooltip.append("text")
		.attr('id', function(d) { return 'nodeInfoTextID' + d.id; })
    	.attr('x', rectNode.width / 2 + tooltip.textMargin)
		.attr('y', rectNode.height / 2 + tooltip.textMargin * 2)
		.attr('width', tooltip.width + 20)
		.attr('height', tooltip.height + 20)
		.attr('class', 'tooltip-text')
		.style('fill', 'black')
		.append("tspan")
	    .text(function(d) {return 'Name: ' + d.name;})
	    .append("tspan")
	    .attr('x', rectNode.width / 2 + tooltip.textMargin)
	    .attr('dy', '1.5em')
	    .text(function(d) {
			// if (d.value) {
			// 	return 'Val: ' + d.value;
			// }
		});

		// Transition nodes to their new position.
		var nodeUpdate = node.transition().duration(duration)
		.attr('transform', function(d) { return 'translate(' + d.y + ',' + d.x + ')'; });
		nodesTooltip.transition().duration(duration)
		.attr('transform', function(d) { return 'translate(' + d.y + ',' + d.x + ')'; });

		nodeUpdate.select('rect')
		.attr('class', function(d) { return d._children ? 'node-rect-closed' : 'node-rect'; })
		.style("stroke", function(d) {
			if(d.class === "found"){
				return white; //red
			}
		})
		.style("stroke-width", function(d) {
			if(d.class === "found"){
				return "2px"; //red
			}
		});

		nodeUpdate.select('text').style('fill-opacity', 1);

		// Transition exiting nodes to the parent's new position
		var nodeExit = node.exit().transition().duration(duration)
			.attr('transform', function(d) { return 'translate(' + source.y + ',' + source.x + ')'; })
			.remove();
		nodesTooltip.exit().transition().duration(duration)
			.attr('transform', function(d) { return 'translate(' + source.y + ',' + source.x + ')'; })
		.remove();

		nodeExit.select('text').style('fill-opacity', 1e-6);


	// 2) ******************* Update the links *******************
		var link = linkGroup.selectAll('path').data(links, function(d) {
			return d.target.id;
		});
		var linkTooltip = linkGroupToolTip.selectAll('g').data(links, function(d) {
			return d.target.id;
		});

		function linkMarkerStart(direction, isSelected) {
			if (direction == 'SYNC')
			{
				return isSelected ? 'url(#start-arrow-selected)' : 'url(#start-arrow)';
			}
			return '';
		}

		function linkType(link) {
			if (link.direction == 'SYNC')
				return "Synchronous [\u2194]";
			else
			{
				if (link.direction == 'ASYN')
					return "Asynchronous [\u2192]";
			}
			return '???';
		}

		d3.selection.prototype.moveToFront = function() {
			  return this.each(function(){
				    this.parentNode.appendChild(this);
				  });
			};

		// Enter any new links at the parent's previous position.
			// Enter any new links at the parent's previous position.
			var linkenter = link.enter().insert('path', 'g')
			.attr('class', 'link')
			.attr('id', function(d) { return 'linkID' + d.target.id; })
			.attr('d', function(d) { return diagonal(d); })
			.attr('marker-end', 'url(#end-arrow)')
			.attr('marker-start', function(d) { return linkMarkerStart(d.target.link.direction, false); })
			.on('mouseover', function(d) {
				d3.select(this).moveToFront();

				d3.select(this).attr('marker-end', 'url(#end-arrow-selected)');
				d3.select(this).attr('marker-start', linkMarkerStart(d.target.link.direction, true));
				d3.select(this).attr('class', 'linkselected');

				$('#tooltipLinkID' + d.target.id).attr('x', (d.target.y + rectNode.width - d.source.y) / 2 + d.source.y);
				$('#tooltipLinkID' + d.target.id).attr('y', (d.target.x - d.source.x) / 2 + d.source.x);
				$('#tooltipLinkID' + d.target.id).css('visibility', 'visible');
				$('#tooltipLinkTextID' + d.target.id).css('visibility', 'visible');
			})
			.on('mouseout', function(d) {
				d3.select(this).attr('marker-end', function(d){
					if(d.class =="found" || d.target.class==="found" ){
						return 'url(#end-arrow-selected)';
					} else {
						return 'url(#end-arrow)';
					}
				  });
				d3.select(this).attr('marker-start', linkMarkerStart(d.target.link.direction, false));
				d3.select(this).attr('class', 'link');
				$('#tooltipLinkID' + d.target.id).css('visibility', 'hidden');
				$('#tooltipLinkTextID' + d.target.id).css('visibility', 'hidden');
			});

			linkTooltip.enter().append('rect')
			.attr('id', function(d) { return 'tooltipLinkID' + d.target.id; })
			.attr('class', 'tooltip-box')
			.style('fill-opacity', 0.8)
			.style('fill', 'white')
			.attr('x', function(d) { return (d.target.y + rectNode.width - d.source.y) / 2 + d.source.y; })
			.attr('y', function(d) { return (d.target.x - d.source.x) / 2 + d.source.x; })
			.attr('width', tooltip.width)
			.attr('height', tooltip.height)
			.on('mouseover', function(d) {
				$('#tooltipLinkID' + d.target.id).css('visibility', 'visible');
				$('#tooltipLinkTextID' + d.target.id).css('visibility', 'visible');
				// After selected a link, the cursor can be hover the tooltip, that's why we still need to highlight the link and the arrow
				$('#linkID' + d.target.id).attr('class', 'linkselected');
				$('#linkID' + d.target.id).attr('marker-end', 'url(#end-arrow-selected)');
				$('#linkID' + d.target.id).attr('marker-start', linkMarkerStart(d.target.link.direction, true));

				removeMouseEvents();
			})
			.on('mouseout', function(d) {
				$('#tooltipLinkID' + d.target.id).css('visibility', 'hidden');
				$('#tooltipLinkTextID' + d.target.id).css('visibility', 'hidden');
				$('#linkID' + d.target.id).attr('class', 'link');
				$('#linkID' + d.target.id).attr('marker-end', 'url(#end-arrow)');
				$('#linkID' + d.target.id).attr('marker-start', linkMarkerStart(d.target.link.direction, false));

				reactivateMouseEvents();
			});

			linkTooltip.enter().append('text')
			.attr('id', function(d) { return 'tooltipLinkTextID' + d.target.id; })
			.attr('class', 'tooltip-text')
			.attr('x', function(d) { return (d.target.y + rectNode.width - d.source.y) / 2 + d.source.y + tooltip.textMargin; })
			.attr('y', function(d) { return (d.target.x - d.source.x) / 2 + d.source.x + tooltip.textMargin * 2; })
			.attr('width', tooltip.width)
			.attr('height', tooltip.height)
			.style('fill', 'black')
			.append("tspan")
	   		// .text(function(d) { return linkType(d.target.link); })
	   		.append("tspan")
	    	.attr('x', function(d) { return (d.target.y + rectNode.width - d.source.y) / 2 + d.source.y + tooltip.textMargin; })
	   		.attr('dy', '1.5em')
	    	.text(function(d) {return d.target.link.name;});

		// Transition links to their new position.
		var linkUpdate = link.transition().duration(duration)
							  .attr('d', function(d) { return diagonal(d); })
							  .attr("marker-end",function(d){
								if(d.class =="found" || d.target.class==="found" ){
									return 'url(#end-arrow-selected)';
								} else {
									return 'url(#end-arrow)';
								}
							  })
							  .style("stroke",function(d){
								if(d.target.class==="found"){
									return red; //"#ff4136";
								}
							  })
							  .style("stroke-width",function(d){
								if(d.target.class==="found"){
									return "3px";
								}
							  });
		linkTooltip.transition().duration(duration)
				   .attr('d', function(d) { return diagonal(d); });

		// Transition exiting nodes to the parent's new position.
		link.exit().transition()
		.remove();

		linkTooltip.exit().transition()
			.remove();

		// Stash the old positions for transition.
		nodes.forEach(function(d) {
			d.x0 = d.x;
			d.y0 = d.y;
		});
	}

	// Zoom functionnality is desactivated (user can use browser Ctrl + mouse wheel shortcut)
	function zoomAndDrag() {
	    //var scale = d3.event.scale,
	    var scale = 1,
	        translation = d3.event.translate,
	        tbound = -height * scale,
	        bbound = height * scale,
	        lbound = (-width + margin.right) * scale,
	        rbound = (width - margin.left) * scale;
	    // limit translation to thresholds
	    translation = [
	        Math.max(Math.min(translation[0], rbound), lbound),
	        Math.max(Math.min(translation[1], bbound), tbound)
	    ];
	    d3.select('.drawarea')
	        .attr('transform', 'translate(' + translation + ')' +
	              ' scale(' + scale + ')');
	}

	function ValidURL(str) {
		var pattern = /^((http|https|ftp):\/\/)/;
		if(pattern.test(str)) {
		  return true;
		}
	  }



	function update_infobox_from_json(d, data) {
		$("#infobox").append("<div id='infoboxInfo'><div class='small_header'>Infobox</div><table id='infoboxTable'><tr><td><h3>Key</h3></td><td><h3>Value</h3></td></tr></table></div>");
		var table = $('#infoboxTable')[0]
		for (var k in data) {
			var key_val = data[k]
			var rowCount = table.rows.length;
			var row = table.insertRow(rowCount);
			var cell1 = row.insertCell(0);
			var cell2 = row.insertCell(1);
			var value_column = '';

			cell1.innerHTML = '<b>' + '<a href="' + k + '">' + k + '</a>' + '</b>';
			key_val.forEach(function(each_node, i){

				if (ValidURL(each_node)) {
					value_column = value_column + '<br><a href="' + each_node + '">' + each_node + '</a>';

				}
				else {
					value_column = value_column + String(each_node);
				}
			});
			cell2.innerHTML = value_column;
			cell2.onclick = function(e) {
				clickLink(d, e);
			};
		}
	}

	function updateInfoBox(d) {
		$('#infobox').empty();

		var parameters = {
			'value' : d.nodeName
		}
		if (d.hasOwnProperty('endpoint')) {
			parameters['endpoint'] = d.endpoint
		}

		get_infobox_json(d, parameters);
		if (paths) {
			$("#infobox").append('<div class="graph_path"><div class="small_header">Path</div></div>');
			paths.forEach(function (node, i) {
				var newSpan = document.createElement("span");
				newSpan.setAttribute('class', 'small_font');
				if (i != paths.length-1) {
					  newSpan.innerHTML = '<a href="javascript:void(0)">' + node.name + '</a> -->';
				} else {
					newSpan.innerHTML = '<a href="javascript:void(0)">' + node.name + '</a>' ;
				}
				newSpan.onclick = function() {
					click(node);
				};
				$(".graph_path").append(newSpan);
			});
		}

		// $("#infobox").append("<div class='small_header'>Infobox</div><table id='infoboxTable'><tr><td><h3>Key</h3></td><td><h3>Value</h3></td></tr></table>");
		// var table = $('#infoboxTable')[0]
		// var key_array = ["link", "parent", "depth", "x", "y", "color", "id", "x0", "y0", "_children", "children", "fixed", "class"];
		// var sorted_keys = Object.keys(d).sort();
		// for (var k in sorted_keys){
		// 	var key_val = sorted_keys[k];
		// 	if (d.hasOwnProperty(key_val) && !key_array.includes(key_val)) {
		// 		var rowCount = table.rows.length;
		// 		var row = table.insertRow(rowCount);
		// 		var cell1 = row.insertCell(0);
		// 		var cell2 = row.insertCell(1);

		// 		cell1.innerHTML = '<b>' + key_val + '</b>';
		// 		if (ValidURL(d[key_val])) {
		// 			cell2.innerHTML = '<a href="' + d[key_val] + '">' + d[key_val] + '</a>';
		// 		} else {
		// 			cell2.innerHTML = d[key_val];
		// 		}
		// 		cell2.onclick = function(e) {
		// 			clickLink(e, d);
		// 		};

		// 	}
		// }

	}

	function get_infobox_json(d, parameters) {
		$(".infoboxspin.spinning-loader").show();
		$.getJSON("/ProvTrack/get_infobox_json/", parameters)
		.done(function(data) {
			console.log( "success", data );
			update_infobox_from_json(d, data.response)
		})
		.fail(function(jqXHR, textStatus, err) {
			console.log( "error", textStatus );
			$('#infobox').text('An error occured in loading the Infobox.');
		})
		.always(function() {
			$(".infoboxspin.spinning-loader").hide();
		});
	}

	function clickLink(d, e) {
		e.preventDefault();
		$("#infoboxInfo").remove();
		var parameters = {
			'value' :  e.target.innerHTML
		};
		if (d.hasOwnProperty('endpoint')) {
			parameters['endpoint'] = d.endpoint
		}
		get_infobox_json(d, parameters);
	}

	// Toggle children on click.
	function click(d) {
		if(typeof(paths) !== "undefined") {
			clearPaths(paths);
		}
		paths = searchTree(root,d.nodeName,[]);
		if(typeof(paths) !== "undefined"){
			clickAction(paths);
		}
		if (d.children) {
			d._children = d.children;
			d.children = null;
		} else {
			d.children = d._children;
			d._children = null;
		}
		update(d);
		updateInfoBox(d);
	}

	function clickAction(paths) {
		for(var i =0;i<paths.length;i++){
			paths[i].class = 'found';
			// if(paths[i]._children){ //if children are hidden: open them, otherwise: don't do anything
			// 	paths[i].children = paths[i]._children;
			// 	paths[i]._children = null;
			// }
			update(paths[i]);
		}
	}

	// Breadth-first traversal of the tree
	// func function is processed on every node of a same level
	// return the max level
	  function breadthFirstTraversal(tree, func)
	  {
		  var max = 0;
		  if (tree && tree.length > 0)
		  {
			  var currentDepth = tree[0].depth;
			  var fifo = [];
			  var currentLevel = [];

			  fifo.push(tree[0]);
			  while (fifo.length > 0) {
				  var node = fifo.shift();
				  if (node.depth > currentDepth) {
					  func(currentLevel);
					  currentDepth++;
					  max = Math.max(max, currentLevel.length);
					  currentLevel = [];
				  }
				  currentLevel.push(node);
				  if (node.children) {
					  for (var j = 0; j < node.children.length; j++) {
						  fifo.push(node.children[j]);
					  }
				  }
		  	}
			func(currentLevel);
			return Math.max(max, currentLevel.length);
		}
		return 0;
	  }

	// x = ordoninates and y = abscissas
	function collision(siblings) {
	  var minPadding = 5;
	  if (siblings) {
		  for (var i = 0; i < siblings.length - 1; i++)
		  {
			  if (siblings[i + 1].x - (siblings[i].x + rectNode.height) < minPadding)
				  siblings[i + 1].x = siblings[i].x + rectNode.height + minPadding;
		  }
	  }
	}

	function removeMouseEvents() {
		// Drag and zoom behaviors are temporarily disabled, so tooltip text can be selected
		mousedown = d3.select('#tree-container').select('svg').on('mousedown.zoom');
		d3.select('#tree-container').select('svg').on("mousedown.zoom", null);
	}

	function reactivateMouseEvents() {
		// Reactivate the drag and zoom behaviors
		d3.select('#tree-container').select('svg').on('mousedown.zoom', mousedown);
	}

	// Name of the event depends of the browser
	function getMouseWheelEvent() {
		if (d3.select('#tree-container').select('svg').on('wheel.zoom'))
		{
			mouseWheelName = 'wheel.zoom';
			return d3.select('#tree-container').select('svg').on('wheel.zoom');
		}
		if (d3.select('#tree-container').select('svg').on('mousewheel.zoom') != null)
		{
			mouseWheelName = 'mousewheel.zoom';
			return d3.select('#tree-container').select('svg').on('mousewheel.zoom');
		}
		if (d3.select('#tree-container').select('svg').on('DOMMouseScroll.zoom'))
		{
			mouseWheelName = 'DOMMouseScroll.zoom';
			return d3.select('#tree-container').select('svg').on('DOMMouseScroll.zoom');
		}
	}

	function diagonal(d) {
		var p0 = {
			x : d.source.x + rectNode.height / 2,
			y : (d.source.y + rectNode.width)
		}, p3 = {
			x : d.target.x + rectNode.height / 2,
			y : d.target.y  - 12 // -12, so the end arrows are just before the rect node
		}, m = (p0.y + p3.y) / 2, p = [ p0, {
			x : p0.x,
			y : m
		}, {
			x : p3.x,
			y : m
		}, p3 ];
		p = p.map(function(d) {
			return [ d.y, d.x ];
		});
		return 'M' + p[0] + 'C' + p[1] + ' ' + p[2] + ' ' + p[3];
	}

	function initDropShadow() {
		var filter = defs.append("filter")
		    .attr("id", "drop-shadow")
		    .attr("color-interpolation-filters", "sRGB");

		filter.append("feOffset")
		.attr("result", "offOut")
		.attr("in", "SourceGraphic")
	    .attr("dx", 0)
	    .attr("dy", 0);

		filter.append("feGaussianBlur")
		    .attr("stdDeviation", 2);

		filter.append("feOffset")
		    .attr("dx", 2)
		    .attr("dy", 2)
		    .attr("result", "shadow");

		filter.append("feComposite")
	    .attr("in", 'offOut')
	    .attr("in2", 'shadow')
	    .attr("operator", "over");
	}

	function initArrowDef() {
		// Build the arrows definitions
		// End arrow
		defs.append('marker')
		.attr('id', 'end-arrow')
		.attr('viewBox', '0 -5 10 10')
		.attr('refX', 0)
		.attr('refY', 0)
		.attr('markerWidth', 6)
		.attr('markerHeight', 6)
		.attr('orient', 'auto')
		.attr('class', 'arrow')
		.append('path')
		.attr('d', 'M0,-5L10,0L0,5');

		// End arrow selected
		defs.append('marker')
		.attr('id', 'end-arrow-selected')
		.attr('viewBox', '0 -5 10 10')
		.attr('refX', 0)
		.attr('refY', 0)
		.attr('markerWidth', 6)
		.attr('markerHeight', 6)
		.attr('orient', 'auto')
		.attr('class', 'arrowselected')
		.append('path')
		.attr('d', 'M0,-5L10,0L0,5');

		// Start arrow
		defs.append('marker')
		.attr('id', 'start-arrow')
		.attr('viewBox', '0 -5 10 10')
		.attr('refX', 0)
		.attr('refY', 0)
		.attr('markerWidth', 6)
		.attr('markerHeight', 6)
		.attr('orient', 'auto')
		.attr('class', 'arrow')
		.append('path')
		.attr('d', 'M10,-5L0,0L10,5');

		// Start arrow selected
		defs.append('marker')
		.attr('id', 'start-arrow-selected')
		.attr('viewBox', '0 -5 10 10')
		.attr('refX', 0)
		.attr('refY', 0)
		.attr('markerWidth', 6)
		.attr('markerHeight', 6)
		.attr('orient', 'auto')
		.attr('class', 'arrowselected')
		.append('path')
		.attr('d', 'M10,-5L0,0L10,5');
	}

	function searchTree(obj,search,path){
		if(obj.nodeName === search){ //if search is found return, add the object to the path and return it
			path.push(obj);
			return path;
		}
		else if(obj.children || obj._children){ //if children are collapsed d3 object will have them instantiated as _children
			var children = (obj.children) ? obj.children : obj._children;
			for(var i=0;i<children.length;i++){
				path.push(obj);// we assume this path is the right one
				var found = searchTree(children[i],search,path);
				if(found){// we were right, this should return the bubbled-up path from the first if statement
					return found;
				}
				else{//we were wrong, remove this parent from the path and continue iterating
					path.pop();
				}
			}
		}
		else{//not the right object, return false so it will continue to iterate in the loop
			return false;
		}
	}

	function extract_select2_data(node,leaves,index){
		if (node.children){
			for(var i = 0;i<node.children.length;i++){
				index = extract_select2_data(node.children[i],leaves,index)[0];
			}
		}
		else {
			leaves.push({id:++index,text:node.nodeName});
		}
		return [index,leaves];
	}

	function openPaths(paths){
		for(var i =0;i<paths.length;i++){
			paths[i].class = 'found';
			if(paths[i]._children){ //if children are hidden: open them, otherwise: don't do anything
				paths[i].children = paths[i]._children;
				paths[i]._children = null;
			}
			update(paths[i]);
		}
	}

	function clearPaths(paths){
		for(var i =0;i<paths.length;i++){
			if (paths[i].class == 'found') {
				paths[i].class = '';
			}
			update(paths[i]);

		}
	}

}
