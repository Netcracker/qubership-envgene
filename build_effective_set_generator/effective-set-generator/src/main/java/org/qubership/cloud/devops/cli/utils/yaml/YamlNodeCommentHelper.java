/*
 * Copyright 2024-2025 NetCracker Technology Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.qubership.cloud.devops.cli.utils.yaml;

import jakarta.enterprise.context.ApplicationScoped;
import org.apache.commons.lang3.StringUtils;
import org.snakeyaml.engine.v2.comments.CommentLine;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.nodes.Node;

import java.util.List;
import java.util.Locale;
import java.util.Optional;

import static org.qubership.cloud.devops.commons.utils.constant.ParametersConstants.SBOM_ORIGIN;

@ApplicationScoped
public class YamlNodeCommentHelper {

    public boolean shouldAddComment(boolean enableTraceability, String origin, boolean deployDescriptorYaml) {
        if (!enableTraceability || StringUtils.isBlank(origin)) {
            return false;
        }
        return !deployDescriptorYaml || !origin.toLowerCase(Locale.ROOT).contains(SBOM_ORIGIN);
    }

    public void moveBlockCommentFromValueToKey(Node valueNode, Node keyNode) {
        List<CommentLine> valueComments = valueNode.getBlockComments();
        if (valueComments == null || valueComments.isEmpty()) {
            return;
        }
        keyNode.setBlockComments(valueComments);
        valueNode.setBlockComments(null);
    }

    public <T extends Node> T attachComment(T node, String origin, boolean addComment, CommentType commentType) {
        if (!addComment) {
            return node;
        }
        CommentLine comment = new CommentLine(Optional.empty(), Optional.empty(), origin, commentType);
        List<CommentLine> comments = List.of(comment);
        if (commentType == CommentType.BLOCK) {
            node.setBlockComments(comments);
        } else {
            node.setInLineComments(comments);
        }
        return node;
    }
}
