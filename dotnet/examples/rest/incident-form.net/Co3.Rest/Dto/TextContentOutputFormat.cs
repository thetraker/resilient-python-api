/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// <auto-generated>
// IBM Resilient REST API version 28.1
//
// Generated by <a href="http://enunciate.webcohesion.com">Enunciate</a>.
// </auto-generated>

using System.Runtime.Serialization;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum TextContentOutputFormat
    {
        /// <summary>
        /// Unspecified enum value.
        /// </summary>
        [JsonIgnore]
        Undefined,

        /// <summary>
        /// <a href="json_TextContentDTO.html">textContentDTO</a> objects are sent to the client as strings.  The string will be in HTML
        /// format if the corresponding field (e.g. incident description, resolution_summary,
        /// etc.) is marked as a rich text field.  If the corresponding field is not marked
        /// as rich text then the string will be in plain text format.
        /// 
        /// <p>Example:</p>
        /// <pre>
        ///  "description": "Text incident description"
        ///  </pre>
        /// </summary>
        [EnumMember(Value = "default")]
        Default,

        /// <summary>
        /// <a href="json_TextContentDTO.html">textContentDTO</a> objects are sent to the client as JSON objects.  The "content" and "format"
        /// properties will be consistent with the corresponding field (e.g. incident
        /// description, resolution summary, etc.) definition.  For example, if the
        /// field is marked as rich text, the "format" will be "html" and the "content"
        /// will be an HTML rendition of the string.  Note that this may require
        /// the server to convert the string.  If the data is stored in the database
        /// as plain text, but the field is a rich text field then the <a href="json_TextContentDTO.html">textContentDTO</a>
        /// data will be converted from plain text to HTML.
        /// 
        /// <p>Example:</p>
        /// <pre>
        ///  "description": {
        ///   "format": "html",
        ///   "content": "&lt;div&gt;Description&lt;/div&gt;"
        ///  }
        ///  </pre>
        /// </summary>
        [EnumMember(Value = "objects_convert")]
        ObjectsConvert,

        /// <summary>
        /// <a href="json_TextContentDTO.html">textContentDTO</a> objects are sent to the client as JSON objects.  The "content" and "format"
        /// properties will be consistent with the way the content is stored in the
        /// database.  The returned content is not related to the field definition, so
        /// text content can be returned for rich text fields and vice-versa.
        /// 
        /// <p>Example:</p>
        /// <pre>
        ///  "description": {
        ///   "format": "html",
        ///   "content": "&lt;div&gt;Description&lt;/div&gt;"
        ///  }
        ///  </pre>
        /// </summary>
        [EnumMember(Value = "objects_no_convert")]
        ObjectsNoConvert,

        /// <summary>
        /// <a href="json_TextContentDTO.html">textContentDTO</a> objects are sent to the client as JSON objects.  The "content" and "format"
        /// properties will be HTML, regardless of the rich text setting in the field definition
        /// and the data storage content.  Note that this may require the server to do a plain text
        /// to HTML conversion.
        /// 
        /// <p>Example:</p>
        /// <pre>
        ///  "description": {
        ///   "format": "html",
        ///   "content": "&lt;div&gt;Description&lt;/div&gt;"
        ///  }
        ///  </pre>
        /// </summary>
        [EnumMember(Value = "objects_convert_html")]
        ObjectsConvertHtml,

        /// <summary>
        /// <a href="json_TextContentDTO.html">textContentDTO</a> objects are sent to the client as JSON objects.  The "content" and "format"
        /// properties will be HTML, regardless of the rich text setting in the field definition
        /// and the data storage format.  Note that this may require the server to do an HTML to
        /// plain text conversion, which will cause formatting to be dropped.
        /// 
        /// <p>Example:</p>
        /// <pre>
        ///  "description": {
        ///   "format": "text",
        ///   "content": "Description"
        ///  }
        ///  </pre>
        /// </summary>
        [EnumMember(Value = "objects_convert_text")]
        ObjectsConvertText,

        /// <summary>
        /// Always output the field as a simple string that is in text format.
        /// </summary>
        [EnumMember(Value = "always_text")]
        AlwaysText
    }
}