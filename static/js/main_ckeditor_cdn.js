/**
 * This configuration was generated using the CKEditor 5 Builder. You can modify it anytime using this link:
 * https://ckeditor.com/ckeditor-5/builder/#installation/NoZgNARATAdAbDADBSBGRAWArCAnIgdgA5FcjViCooDFCbEoiCMQo3UQtcNepEiKCAC8AFgFoAxgDsUUMMFRhEYJUpWoAupACGAMx2I8BCJqA===
 */

const {
	BalloonEditor,
	Autoformat,
	AutoImage,
	AutoLink,
	Autosave,
	BlockQuote,
	BlockToolbar,
	Bold,
	CloudServices,
	Code,
	CodeBlock,
	Emoji,
	Essentials,
	FindAndReplace,
	Heading,
	Highlight,
	HorizontalLine,
	ImageBlock,
	ImageInline,
	ImageInsert,
	ImageInsertViaUrl,
	ImageResize,
	ImageStyle,
	ImageToolbar,
	ImageUpload,
	Indent,
	IndentBlock,
	Italic,
	Link,
	LinkImage,
	List,
	ListProperties,
	Markdown,
	MediaEmbed,
	Mention,
	PageBreak,
	Paragraph,
	PasteFromMarkdownExperimental,
	PasteFromOffice,
	PlainTableOutput,
	SimpleUploadAdapter,
	SpecialCharacters,
	SpecialCharactersArrows,
	SpecialCharactersCurrency,
	SpecialCharactersEssentials,
	SpecialCharactersLatin,
	SpecialCharactersMathematical,
	SpecialCharactersText,
	Strikethrough,
	Table,
	TableCaption,
	TableCellProperties,
	TableColumnResize,
	TableLayout,
	TableProperties,
	TableToolbar,
	TextTransformation,
	Title,
	TodoList,
	Underline
} = window.CKEDITOR;

const LICENSE_KEY =
	'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NDkxNjc5OTksImp0aSI6IjFjNzk5NzJjLTE1NmItNGFlNS05NmQwLWI3N2JiODA5YmU3NiIsInVzYWdlRW5kcG9pbnQiOiJodHRwczovL3Byb3h5LWV2ZW50LmNrZWRpdG9yLmNvbSIsImRpc3RyaWJ1dGlvbkNoYW5uZWwiOlsiY2xvdWQiLCJkcnVwYWwiLCJzaCJdLCJ3aGl0ZUxhYmVsIjp0cnVlLCJsaWNlbnNlVHlwZSI6InRyaWFsIiwiZmVhdHVyZXMiOlsiKiJdLCJ2YyI6Ijk3YmFiOWIxIn0.QX_uegc-lMvdJ9ZdbjzZzXCsnVC_Rmw3aJXLNSXFLLuG4ZnTeX51txesTARYocmhDnvgtW_mdcXHYGLcVoVpQg';

const editorConfig = {
	toolbar: {
		items: [
			'undo',
			'redo',
			'|',
			'findAndReplace',
			'|',
			'heading',
			'|',
			'bold',
			'italic',
			'underline',
			'strikethrough',
			'code',
			'|',
			'emoji',
			'specialCharacters',
			'horizontalLine',
			'pageBreak',
			'link',
			'insertImage',
			'mediaEmbed',
			'insertTable',
			'insertTableLayout',
			'highlight',
			'blockQuote',
			'codeBlock',
			'|',
			'bulletedList',
			'numberedList',
			'todoList',
			'outdent',
			'indent'
		],
		shouldNotGroupWhenFull: false
	},
	plugins: [
		Autoformat,
		AutoImage,
		AutoLink,
		Autosave,
		BlockQuote,
		BlockToolbar,
		Bold,
		CloudServices,
		Code,
		CodeBlock,
		Emoji,
		Essentials,
		FindAndReplace,
		Heading,
		Highlight,
		HorizontalLine,
		ImageBlock,
		ImageInline,
		ImageInsert,
		ImageInsertViaUrl,
		ImageResize,
		ImageStyle,
		ImageToolbar,
		ImageUpload,
		Indent,
		IndentBlock,
		Italic,
		Link,
		LinkImage,
		List,
		ListProperties,
		Markdown,
		MediaEmbed,
		Mention,
		PageBreak,
		Paragraph,
		PasteFromMarkdownExperimental,
		PasteFromOffice,
		PlainTableOutput,
		SimpleUploadAdapter,
		SpecialCharacters,
		SpecialCharactersArrows,
		SpecialCharactersCurrency,
		SpecialCharactersEssentials,
		SpecialCharactersLatin,
		SpecialCharactersMathematical,
		SpecialCharactersText,
		Strikethrough,
		Table,
		TableCaption,
		TableCellProperties,
		TableColumnResize,
		TableLayout,
		TableProperties,
		TableToolbar,
		TextTransformation,
		Title,
		TodoList,
		Underline
	],
	blockToolbar: [
		'bold',
		'italic',
		'|',
		'link',
		'insertImage',
		'insertTable',
		'insertTableLayout',
		'|',
		'bulletedList',
		'numberedList',
		'outdent',
		'indent'
	],
	heading: {
		options: [
			{
				model: 'paragraph',
				title: 'Paragraph',
				class: 'ck-heading_paragraph'
			},
			{
				model: 'heading1',
				view: 'h1',
				title: 'Heading 1',
				class: 'ck-heading_heading1'
			},
			{
				model: 'heading2',
				view: 'h2',
				title: 'Heading 2',
				class: 'ck-heading_heading2'
			},
			{
				model: 'heading3',
				view: 'h3',
				title: 'Heading 3',
				class: 'ck-heading_heading3'
			},
			{
				model: 'heading4',
				view: 'h4',
				title: 'Heading 4',
				class: 'ck-heading_heading4'
			},
			{
				model: 'heading5',
				view: 'h5',
				title: 'Heading 5',
				class: 'ck-heading_heading5'
			},
			{
				model: 'heading6',
				view: 'h6',
				title: 'Heading 6',
				class: 'ck-heading_heading6'
			}
		]
	},
	image: {
		toolbar: ['imageStyle:inline', 'imageStyle:wrapText', 'imageStyle:breakText', '|', 'resizeImage']
	},
	// initialData:'',
	language: 'zh-cn',
	licenseKey: LICENSE_KEY,
	link: {
		addTargetToExternalLinks: true,
		defaultProtocol: 'https://',
		decorators: {
			toggleDownloadable: {
				mode: 'manual',
				label: 'Downloadable',
				attributes: {
					download: 'file'
				}
			}
		}
	},
	list: {
		properties: {
			styles: true,
			startIndex: true,
			reversed: true
		}
	},
	mention: {
		feeds: [
			{
				marker: '@',
				feed: [
					/* See: https://ckeditor.com/docs/ckeditor5/latest/features/mentions.html */
				]
			}
		]
	},
	placeholder: 'Type or paste your content here!',
	table: {
		contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells', 'tableProperties', 'tableCellProperties']
	}
};
